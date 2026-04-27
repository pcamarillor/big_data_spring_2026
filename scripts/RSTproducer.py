"""
Synthetic Ride-Sharing Trip Dataset Producer
============================================
Procesamiento de Datos Masivos | ITESO | Santiago Ortiz Soto

Object-oriented version.

This script generates a large synthetic ride-sharing trip dataset in JSON Lines
(.jsonl) format. Each line in the output files is one JSON object representing
one Uber/Lyft-style ride-sharing trip.

The script is designed for a big data pipeline where:

    RSTproducer.py -> S3 raw JSONL data -> EMR Spark job -> S3 Parquet output

The producer supports two execution modes:

1. local mode:
   Writes JSONL files to a local directory. This is useful for testing the
   script with a smaller dataset before generating the full 30 GB required by
   the project.

2. cloud mode:
   Generates JSONL files in a temporary local directory and uploads each part
   file to an Amazon S3 bucket. This is the recommended mode for the final
   project because the required dataset is large.

Recommended cloud usage on EC2 or EMR primary node:
  python3 RSTproducer.py cloud \
    --bucket your-bucket \
    --prefix raw/rideshare_trips \
    --target-gb 30 \
    --file-size-mb 256

Local test usage:
  python3 RSTproducer.py local \
    --location ./rideshare_trips \
    --target-gb 1 \
    --file-size-mb 128 \
    --allow-small-test

Dependencies:
  pip3 install faker boto3

Notes:
- Faker is used to create realistic timestamps and random identifiers.
- boto3 is only required when using cloud mode to upload files to S3.
- The script intentionally creates a small percentage of bad/null values so
  the Spark pipeline can demonstrate cleaning transformations later.
"""

import argparse
import json
import math
import random
import tempfile
import time
import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple

from faker import Faker


# ─────────────────────────────────────────────
# Constants
# ─────────────────────────────────────────────
# These constants convert user-friendly storage units into bytes.
# The producer writes files based on byte counts because file systems and S3
# measure object sizes in bytes.
BYTES_PER_MB = 1024 * 1024
BYTES_PER_GB = 1024 * 1024 * 1024

# The project requires at least 30 GB of raw data.
# The script blocks smaller production runs unless --allow-small-test is used.
MIN_PROJECT_GB = 30

# Dictionary that maps each city to realistic pickup/dropoff zones.
# These values make the dataset more useful for Spark transformations such as:
# grouping by city, joining with a zone dimension table, and partition analysis.
CITY_ZONES: Dict[str, List[str]] = {
    "Guadalajara": ["Centro", "Providencia", "Americana", "Chapultepec", "Oblatos"],
    "Zapopan": ["Andares", "Chapalita", "Ciudad Granja", "Valle Real", "Tesistan"],
    "Tlaquepaque": ["Centro", "Forum", "Las Juntas", "Santa Anita", "El Alamo"],
    "Tonalá": ["Centro", "Loma Dorada", "Jauja", "Coyula", "Puente Grande"],
    "Tlajomulco": ["Santa Fe", "Cajititlan", "San Agustin", "La Rioja", "El Palomar"],
}

# Categorical values used in the generated trip records.
# These fields are useful for filtering, grouping, aggregating, and analyzing
# payment behavior, vehicle type, trip status, and weather impact.
PAYMENT_METHODS = ["credit_card", "debit_card", "cash", "wallet", "corporate_account"]
VEHICLE_TYPES = ["standard", "comfort", "xl", "green", "premium"]

# "completed" appears multiple times to make completed trips more common than
# cancelled or no-show trips. This creates a realistic distribution because most
# ride-sharing requests become completed trips.
TRIP_STATUSES = ["completed", "completed", "completed", "completed", "cancelled", "no_show"]

WEATHER_CONDITIONS = ["clear", "cloudy", "rain", "storm", "fog", "hot"]

# These probabilities intentionally introduce small data quality problems.
# The Spark application can later clean these records by filling nulls,
# removing negative values, or filtering invalid rows.
NULL_PAYMENT_PROBABILITY = 0.01
BAD_DISTANCE_PROBABILITY = 0.002
BAD_FARE_PROBABILITY = 0.001


# ─────────────────────────────────────────────
# Configuration objects
# ─────────────────────────────────────────────
@dataclass(frozen=True)
class ProducerConfig:
    """
    Stores and validates the main size configuration for the producer.

    This class is marked as a frozen dataclass, which means its values cannot
    be changed after the object is created. That is useful because the target
    size and file size should remain stable during a generation run.

    Attributes:
        target_gb:
            Total amount of raw JSONL data to generate, measured in GB.
            For the final project, this should be at least 30.

        file_size_mb:
            Approximate size of each generated JSONL part file, measured in MB.
            For example, 256 MB creates many medium-sized files instead of one
            huge file, which is better for Spark parallel processing.

        allow_small_test:
            When False, the script enforces the 30 GB minimum.
            When True, smaller test datasets are allowed. This should only be
            used for local testing, not for the final project run.
    """

    target_gb: float
    file_size_mb: int
    allow_small_test: bool = False

    @property
    def target_bytes(self) -> float:
        """
        Convert the requested target size from GB to bytes.

        The rest of the script uses bytes because generated records are written
        as encoded bytes to disk.
        """
        return self.target_gb * BYTES_PER_GB

    @property
    def file_target_bytes(self) -> int:
        """
        Convert the requested part-file size from MB to bytes.

        Each generated output file will be written until it reaches at least
        this many bytes.
        """
        return self.file_size_mb * BYTES_PER_MB

    @property
    def files_needed(self) -> int:
        """
        Calculate how many JSONL part files are required.

        Example:
            30 GB / 256 MB = approximately 120 files

        math.ceil is used so the generated dataset reaches or slightly exceeds
        the requested target size instead of falling short.
        """
        return math.ceil(self.target_bytes / self.file_target_bytes)

    def validate(self) -> None:
        """
        Validate the size configuration before any data is generated.

        This prevents accidentally producing a dataset that is too small for the
        final project. A smaller dataset is only allowed when --allow-small-test
        is explicitly provided.
        """
        if self.target_gb < MIN_PROJECT_GB and not self.allow_small_test:
            raise SystemExit(
                f"This project requires at least {MIN_PROJECT_GB} GB. "
                f"Use --target-gb {MIN_PROJECT_GB} or add --allow-small-test for local testing."
            )

        if self.file_size_mb <= 0:
            raise SystemExit("--file-size-mb must be greater than 0")


@dataclass(frozen=True)
class GenerationSummary:
    """
    Stores the final metrics of a producer execution.

    This class is used after the run finishes to report how much data was
    generated, how many records were created, and how long the process took.

    Attributes:
        total_bytes:
            Total number of bytes written across all generated JSONL files.

        total_records:
            Total number of ride-sharing trip records generated.

        elapsed_seconds:
            Total execution time in seconds.
    """

    total_bytes: int
    total_records: int
    elapsed_seconds: float

    def print(self) -> None:
        """
        Print the final run summary in a readable format.

        The size is converted from bytes back to GB so it is easy to confirm
        whether the 30 GB requirement was met.
        """
        print("\nDone.")
        print(f"Total size       : {self.total_bytes / BYTES_PER_GB:.2f} GB")
        print(f"Total records    : {self.total_records:,}")
        print(f"Elapsed seconds  : {self.elapsed_seconds:.2f}")


# ─────────────────────────────────────────────
# Trip generation
# ─────────────────────────────────────────────
class RideShareTripGenerator:
    """
    Responsible for creating synthetic ride-sharing trip records.

    This class focuses only on data generation. It does not know where the data
    will be saved. That separation keeps the code cleaner because the same
    generator can be used by both the local producer and the cloud producer.

    Main responsibilities:
    - Select random pickup and dropoff locations.
    - Generate realistic trip timestamps.
    - Generate distance, fare, tip, status, vehicle type, and weather fields.
    - Intentionally create a small number of bad/null values for cleaning tests.
    - Convert each generated dictionary into JSONL-ready bytes.

    Output:
        A Python dictionary for each trip, later serialized as one JSON object
        per line in a .jsonl file.
    """

    def __init__(self, seed: int = 42) -> None:
        """
        Initialize Faker and Python's random module with a fixed seed.

        Using a seed makes the generated data reproducible. Reproducibility is
        useful in academic projects because the same script can generate similar
        data patterns across multiple runs.
        """
        self.fake = Faker()
        Faker.seed(seed)
        random.seed(seed)

    def random_city_zone(self) -> Tuple[str, str]:
        """
        Select a random city and one zone inside that city.

        Returns:
            A tuple in the form:
                (city, zone)

        Example:
            ("Guadalajara", "Centro")
        """
        city = random.choice(list(CITY_ZONES.keys()))
        zone = random.choice(CITY_ZONES[city])
        return city, zone

    @staticmethod
    def isoformat(dt: datetime) -> str:
        """
        Convert a datetime object into a clean ISO-8601 timestamp string.

        Microseconds are removed to make the generated timestamps cleaner and
        easier to read in JSON files and Spark DataFrames.
        """
        return dt.replace(microsecond=0).isoformat()

    def generate_trip(self) -> Dict[str, object]:
        """
        Generate one synthetic ride-sharing trip record.

        The generated record contains the main fields expected in the project:
        trip identifiers, timestamps, rider/driver IDs, pickup/dropoff
        locations, distance, fare, tip, payment method, vehicle type, status,
        weather, and surge multiplier.

        Data quality behavior:
        - Most records are completed trips.
        - Cancelled and no-show trips have no dropoff timestamp.
        - Some records intentionally have negative distance or fare values.
        - Some records intentionally have a null payment method.

        These imperfect values help demonstrate Spark cleaning transformations.
        """
        # Select pickup and dropoff city/zone pairs.
        pickup_city, pickup_zone = self.random_city_zone()
        dropoff_city, dropoff_zone = self.random_city_zone()

        # Generate a random request timestamp within the project date range.
        request_ts = self.fake.date_time_between(
            start_date=datetime(2026, 1, 1, tzinfo=timezone.utc),
            end_date=datetime(2026, 4, 30, 23, 59, 59, tzinfo=timezone.utc),
        )

        # Simulate the time between requesting a ride and driver pickup.
        wait_minutes = random.randint(1, 18)

        # Simulate trip duration after pickup.
        duration_minutes = random.randint(4, 95)

        pickup_ts = request_ts + timedelta(minutes=wait_minutes)
        dropoff_ts: Optional[datetime] = pickup_ts + timedelta(minutes=duration_minutes)

        # Generate core trip economics.
        distance_km = round(random.uniform(0.4, 45.0), 2)
        surge_multiplier = random.choice([1.0, 1.0, 1.0, 1.1, 1.2, 1.4, 1.7, 2.0])
        base_fare = 28.0

        # Fare is based on a base amount, distance, and possible surge pricing.
        fare_amount = round(
            (base_fare + distance_km * random.uniform(7.5, 14.5)) * surge_multiplier,
            2,
        )

        # Most trips have no tip. Some trips have a random tip.
        tip_amount = round(random.choice([0, 0, 0, random.uniform(5, 80)]), 2)

        # Decide whether the trip was completed, cancelled, or no-show.
        trip_status = random.choice(TRIP_STATUSES)

        # Cancelled/no-show trips should not have a dropoff timestamp and should
        # have smaller fare values because the ride was not completed.
        if trip_status != "completed":
            dropoff_ts = None
            fare_amount = round(random.uniform(0, 45), 2)
            tip_amount = 0.0

        # Intentionally create a small number of invalid distance values.
        # The Spark pipeline can later filter these out.
        if random.random() < BAD_DISTANCE_PROBABILITY:
            distance_km = -distance_km

        # Intentionally create a small number of invalid fare values.
        # The Spark pipeline can later filter these out.
        if random.random() < BAD_FARE_PROBABILITY:
            fare_amount = -fare_amount

        # Select a payment method, with a small chance of null.
        # Null values allow the Spark pipeline to demonstrate fill/drop logic.
        payment_method = random.choice(PAYMENT_METHODS)
        if random.random() < NULL_PAYMENT_PROBABILITY:
            payment_method = None

        # Return a complete trip record as a dictionary.
        # This dictionary is later converted to one JSON object in the JSONL file.
        return {
            "trip_id": str(uuid.uuid4()),
            "request_timestamp": self.isoformat(request_ts),
            "pickup_timestamp": self.isoformat(pickup_ts),
            "dropoff_timestamp": self.isoformat(dropoff_ts) if dropoff_ts else None,
            "rider_id": f"rider_{self.fake.random_int(min=1, max=2_000_000)}",
            "driver_id": f"driver_{self.fake.random_int(min=1, max=250_000)}",
            "pickup_city": pickup_city,
            "pickup_zone": pickup_zone,
            "dropoff_city": dropoff_city,
            "dropoff_zone": dropoff_zone,
            "trip_distance_km": distance_km,
            "fare_amount": fare_amount,
            "tip_amount": tip_amount,
            "payment_method": payment_method,
            "vehicle_type": random.choice(VEHICLE_TYPES),
            "trip_status": trip_status,
            "weather_condition": random.choice(WEATHER_CONDITIONS),
            "surge_multiplier": surge_multiplier,
        }

    def jsonl_records(self) -> Iterable[bytes]:
        """
        Yield JSONL records forever as encoded bytes.

        This method is an infinite generator. It keeps producing records until
        the file writer decides it has written enough bytes for the current
        part file.

        Why bytes?
            The writer tracks file size in bytes to make sure each part file
            reaches the requested target size.

        Why JSON Lines?
            JSONL is convenient for Spark because each line is an independent
            JSON object. Spark can read a folder of JSONL files in parallel.
        """
        while True:
            record = json.dumps(self.generate_trip(), separators=(",", ":")) + "\n"
            yield record.encode("utf-8")


# ─────────────────────────────────────────────
# File writing
# ─────────────────────────────────────────────
class JsonlFileWriter:
    """
    Responsible for writing generated records into JSONL part files.

    This class does not generate trip data itself. Instead, it receives a
    RideShareTripGenerator object and asks it for JSONL records.

    Main responsibilities:
    - Create deterministic part-file names.
    - Write records to disk.
    - Stop writing when the file reaches the target byte size.
    - Return file-level metrics such as bytes written and record count.

    Keeping file writing separate from trip generation makes the script easier
    to maintain and easier to extend.
    """

    def __init__(self, generator: RideShareTripGenerator) -> None:
        """
        Store the trip generator used to produce JSONL records.
        """
        self.generator = generator

    @staticmethod
    def make_filename(index: int) -> str:
        """
        Create a deterministic filename for a JSONL part file.

        The index is padded with zeros so files sort correctly in S3 and local
        file listings.

        Example:
            index=1   -> trips_part_00001.jsonl
            index=120 -> trips_part_00120.jsonl
        """
        return f"trips_part_{index:05d}.jsonl"

    def write_file(self, path: Path, target_bytes: int) -> Tuple[int, int]:
        """
        Write JSONL records to one file until the target size is reached.

        Args:
            path:
                Local file path where the JSONL part file will be written.

            target_bytes:
                Minimum number of bytes that this file should contain.

        Returns:
            A tuple:
                (bytes_written, records_written)

        Important:
            The final file can be slightly larger than target_bytes because the
            method finishes writing the current JSONL record before stopping.
        """
        bytes_written = 0
        records_written = 0

        # Open the file in binary mode because jsonl_records() yields bytes.
        with path.open("wb") as output:
            for record in self.generator.jsonl_records():
                output.write(record)
                bytes_written += len(record)
                records_written += 1

                # Stop once the file reaches or exceeds the configured size.
                if bytes_written >= target_bytes:
                    break

        return bytes_written, records_written


# ─────────────────────────────────────────────
# Producer base class
# ─────────────────────────────────────────────
class DatasetProducer(ABC):
    """
    Abstract base class that defines the shared producer workflow.

    This is the parent class for both:
    - LocalDatasetProducer
    - CloudDatasetProducer

    The purpose of this class is to avoid duplicating the same generation loop
    in both local and cloud modes.

    Shared workflow handled by this class:
    1. Validate the configuration.
    2. Print startup information.
    3. Loop through the number of required part files.
    4. Generate and store each part file.
    5. Track total bytes and total records.
    6. Print progress after every part file.
    7. Return and print a final GenerationSummary.

    Output-specific behavior is intentionally left to child classes:
    - LocalDatasetProducer stores files in a local directory.
    - CloudDatasetProducer uploads files to S3.

    This is why the class uses abstract methods. Any child class must implement
    print_header(), process_part(), and print_progress().
    """

    mode_name = "base"

    def __init__(self, config: ProducerConfig, writer: JsonlFileWriter) -> None:
        """
        Store shared dependencies needed by all producer types.

        Args:
            config:
                ProducerConfig object containing target size and part-file size.

            writer:
                JsonlFileWriter object responsible for writing JSONL files.
        """
        self.config = config
        self.writer = writer

    def run(self) -> GenerationSummary:
        """
        Execute the complete dataset generation process.

        This method contains the template algorithm used by all producers.
        Child classes customize only the storage-specific parts through
        process_part() and progress/header methods.

        Returns:
            GenerationSummary containing total size, total records, and runtime.
        """
        self.config.validate()
        self.print_header()

        total_bytes = 0
        total_records = 0
        start = time.time()

        # Generate each required part file.
        # The number of files is calculated from target_gb and file_size_mb.
        for index in range(1, self.config.files_needed + 1):
            bytes_written, records_written = self.process_part(index)
            total_bytes += bytes_written
            total_records += records_written
            self.print_progress(index, bytes_written, records_written, total_bytes)

        elapsed = time.time() - start

        # Create and print a final summary object.
        summary = GenerationSummary(total_bytes, total_records, elapsed)
        summary.print()
        return summary

    @abstractmethod
    def print_header(self) -> None:
        """
        Print startup information for the selected producer mode.

        Local and cloud modes display different information, so this method is
        implemented by each child class.
        """
        pass

    @abstractmethod
    def process_part(self, index: int) -> Tuple[int, int]:
        """
        Generate and store one JSONL part file.

        Args:
            index:
                Part-file number, starting at 1.

        Returns:
            A tuple:
                (bytes_written, records_written)

        The local implementation writes directly to a local folder.
        The cloud implementation writes to a temporary file and uploads it to S3.
        """
        pass

    @abstractmethod
    def print_progress(
        self,
        index: int,
        bytes_written: int,
        records_written: int,
        total_bytes: int,
    ) -> None:
        """
        Print progress after one part file has been processed.

        Each child class prints a message that makes sense for its destination:
        local path for local mode, S3 URI for cloud mode.
        """
        pass


# ─────────────────────────────────────────────
# Local producer
# ─────────────────────────────────────────────
class LocalDatasetProducer(DatasetProducer):
    """
    Producer implementation for local filesystem output.

    This class is used when the user runs:

        python3 RSTproducer.py local ...

    Main responsibilities:
    - Create the local output directory if it does not exist.
    - Generate JSONL part files directly inside that directory.
    - Print progress using local file paths.

    This mode is mainly useful for testing because generating the full 30 GB
    dataset locally may take significant disk space.
    """

    mode_name = "local"

    def __init__(self, config: ProducerConfig, writer: JsonlFileWriter, output_dir: Path) -> None:
        """
        Initialize the local producer.

        Args:
            config:
                Shared producer configuration.

            writer:
                JSONL file writer.

            output_dir:
                Local directory where generated JSONL files will be stored.
        """
        super().__init__(config, writer)
        self.output_dir = output_dir

    def print_header(self) -> None:
        """
        Create the output directory and print local-mode startup settings.
        """
        self.output_dir.mkdir(parents=True, exist_ok=True)

        print("Mode             : local")
        print(f"Output directory : {self.output_dir}")
        print(f"Target size      : {self.config.target_gb} GB")
        print(f"Part file size   : {self.config.file_size_mb} MB")
        print(f"Files planned    : {self.config.files_needed}\n")

    def process_part(self, index: int) -> Tuple[int, int]:
        """
        Generate one JSONL part file in the local output directory.

        Args:
            index:
                Current part-file number.

        Returns:
            A tuple:
                (bytes_written, records_written)
        """
        filename = self.writer.make_filename(index)
        path = self.output_dir / filename
        return self.writer.write_file(path, self.config.file_target_bytes)

    def print_progress(
        self,
        index: int,
        bytes_written: int,
        records_written: int,
        total_bytes: int,
    ) -> None:
        """
        Print progress for a locally written part file.
        """
        path = self.output_dir / self.writer.make_filename(index)
        print(
            f"[{index}/{self.config.files_needed}] Written {path} | "
            f"{bytes_written / BYTES_PER_MB:.2f} MB | "
            f"{records_written:,} records | "
            f"total {total_bytes / BYTES_PER_GB:.2f} GB"
        )


# ─────────────────────────────────────────────
# Cloud producer
# ─────────────────────────────────────────────
class CloudDatasetProducer(DatasetProducer):
    """
    Producer implementation for Amazon S3 output.

    This class is used when the user runs:

        python3 RSTproducer.py cloud ...

    Main responsibilities:
    - Create a boto3 S3 client.
    - Create a temporary local directory.
    - Generate one JSONL part file at a time.
    - Upload each part file to the configured S3 bucket and prefix.
    - Delete the temporary local file after upload.
    - Print progress using S3 paths.

    The temporary-file approach avoids keeping the full 30 GB dataset on the
    EC2 or EMR node at the same time. Only one part file needs to exist locally
    before it is uploaded and removed.
    """

    mode_name = "cloud"

    def __init__(
        self,
        config: ProducerConfig,
        writer: JsonlFileWriter,
        bucket: str,
        prefix: str,
    ) -> None:
        """
        Initialize the cloud producer.

        Args:
            config:
                Shared producer configuration.

            writer:
                JSONL file writer.

            bucket:
                Name of the target S3 bucket.

            prefix:
                S3 folder/prefix where the JSONL part files will be uploaded.
                Example:
                    raw/rideshare_trips
        """
        super().__init__(config, writer)
        self.bucket = bucket
        self.prefix = prefix.strip("/")
        self.s3 = self._create_s3_client()
        self.tmp_path: Optional[Path] = None

    @staticmethod
    def _create_s3_client():
        """
        Create and return a boto3 S3 client.

        boto3 is imported inside this method so local mode does not require S3
        dependencies unless cloud mode is actually used.
        """
        try:
            import boto3
        except ImportError:
            raise SystemExit("boto3 is not installed. Run: pip3 install boto3")

        return boto3.client("s3")

    def run(self) -> GenerationSummary:
        """
        Run the cloud producer using a temporary local directory.

        The temporary directory is automatically deleted when the with-block
        finishes. During the run, each generated file is uploaded to S3 and then
        removed from the temporary directory.
        """
        with tempfile.TemporaryDirectory(prefix="rideshare_producer_") as tmpdir:
            self.tmp_path = Path(tmpdir)
            return super().run()

    def print_header(self) -> None:
        """
        Print cloud-mode startup settings.
        """
        print("Mode             : cloud")
        print(f"Bucket           : {self.bucket}")
        print(f"Prefix           : {self.prefix}")
        print(f"Target size      : {self.config.target_gb} GB")
        print(f"Part file size   : {self.config.file_size_mb} MB")
        print(f"Files planned    : {self.config.files_needed}\n")

    def process_part(self, index: int) -> Tuple[int, int]:
        """
        Generate one JSONL part file, upload it to S3, and delete the local copy.

        Args:
            index:
                Current part-file number.

        Returns:
            A tuple:
                (bytes_written, records_written)
        """
        if self.tmp_path is None:
            raise RuntimeError("Temporary path was not initialized.")

        filename = self.writer.make_filename(index)
        local_path = self.tmp_path / filename
        key = self.s3_key(filename)

        # Write the JSONL part file locally first.
        bytes_written, records_written = self.writer.write_file(
            local_path,
            self.config.file_target_bytes,
        )

        # Upload the finished part file to S3.
        self.s3.upload_file(str(local_path), self.bucket, key)

        # Delete the local temporary file to save disk space.
        local_path.unlink(missing_ok=True)

        return bytes_written, records_written

    def s3_key(self, filename: str) -> str:
        """
        Build the full S3 object key for a generated filename.

        Example:
            prefix = "raw/rideshare_trips"
            filename = "trips_part_00001.jsonl"

            result:
            "raw/rideshare_trips/trips_part_00001.jsonl"
        """
        return f"{self.prefix}/{filename}" if self.prefix else filename

    def print_progress(
        self,
        index: int,
        bytes_written: int,
        records_written: int,
        total_bytes: int,
    ) -> None:
        """
        Print progress for an uploaded S3 part file.
        """
        filename = self.writer.make_filename(index)
        key = self.s3_key(filename)

        print(
            f"[{index}/{self.config.files_needed}] Uploaded s3://{self.bucket}/{key} | "
            f"{bytes_written / BYTES_PER_MB:.2f} MB | "
            f"{records_written:,} records | "
            f"total {total_bytes / BYTES_PER_GB:.2f} GB"
        )


# ─────────────────────────────────────────────
# CLI application
# ─────────────────────────────────────────────
class ProducerCLI:
    """
    Command-line interface for the dataset producer.

    This class separates command-line parsing from the actual data generation
    logic. It decides which producer implementation should be created based on
    the selected command:

        local -> LocalDatasetProducer
        cloud -> CloudDatasetProducer

    Main responsibilities:
    - Define the command-line arguments.
    - Parse user input.
    - Create the ProducerConfig object.
    - Create the shared RideShareTripGenerator and JsonlFileWriter objects.
    - Instantiate the correct producer class.
    - Start the generation run.
    """

    def build_parser(self) -> argparse.ArgumentParser:
        """
        Build and return the argparse command-line parser.

        The parser has two subcommands:
        - local
        - cloud

        Both subcommands share these arguments:
        - --target-gb
        - --file-size-mb
        - --allow-small-test

        The local subcommand also has:
        - --location

        The cloud subcommand also has:
        - --bucket
        - --prefix
        """
        parser = argparse.ArgumentParser(
            description="Generate a synthetic ride-sharing trip dataset as JSONL files."
        )
        subparsers = parser.add_subparsers(dest="mode", required=True)

        # Local mode arguments.
        local_parser = subparsers.add_parser(
            "local",
            help="Write JSONL files to a local directory.",
        )
        local_parser.add_argument(
            "--location",
            default="./rideshare_trips",
            help="Directory where JSONL files will be saved. Default: ./rideshare_trips.",
        )
        self.add_shared_arguments(local_parser)

        # Cloud mode arguments.
        cloud_parser = subparsers.add_parser(
            "cloud",
            help="Generate JSONL files and upload them to S3.",
        )
        cloud_parser.add_argument("--bucket", required=True, help="S3 bucket name.")
        cloud_parser.add_argument(
            "--prefix",
            default="raw/rideshare_trips",
            help="S3 key prefix for uploaded JSONL files. Default: raw/rideshare_trips.",
        )
        self.add_shared_arguments(cloud_parser)

        return parser

    @staticmethod
    def add_shared_arguments(parser: argparse.ArgumentParser) -> None:
        """
        Add arguments that are used by both local and cloud modes.
        """
        parser.add_argument(
            "--target-gb",
            type=float,
            default=30,
            help="Total raw JSONL data size to generate in GB. Default: 30.",
        )
        parser.add_argument(
            "--file-size-mb",
            type=int,
            default=256,
            help="Approximate size of each generated JSONL part file in MB. Default: 256.",
        )
        parser.add_argument(
            "--allow-small-test",
            action="store_true",
            help="Allow target sizes below 30 GB for quick local testing.",
        )

    def create_config(self, args: argparse.Namespace) -> ProducerConfig:
        """
        Create a ProducerConfig object from parsed command-line arguments.
        """
        return ProducerConfig(
            target_gb=args.target_gb,
            file_size_mb=args.file_size_mb,
            allow_small_test=args.allow_small_test,
        )

    def create_producer(self, args: argparse.Namespace) -> DatasetProducer:
        """
        Create and return the correct producer object based on the selected mode.

        This method wires together all major objects:
        - ProducerConfig controls size settings.
        - RideShareTripGenerator creates trip records.
        - JsonlFileWriter writes records into JSONL files.
        - LocalDatasetProducer or CloudDatasetProducer stores the files.

        Returns:
            A DatasetProducer child object.
        """
        config = self.create_config(args)
        generator = RideShareTripGenerator(seed=42)
        writer = JsonlFileWriter(generator)

        if args.mode == "local":
            return LocalDatasetProducer(
                config=config,
                writer=writer,
                output_dir=Path(args.location),
            )

        if args.mode == "cloud":
            return CloudDatasetProducer(
                config=config,
                writer=writer,
                bucket=args.bucket,
                prefix=args.prefix,
            )

        raise SystemExit(f"Unknown mode: {args.mode}")

    def run(self) -> None:
        """
        Parse command-line arguments, create the producer, and start generation.
        """
        args = self.build_parser().parse_args()
        producer = self.create_producer(args)
        producer.run()


# ─────────────────────────────────────────────
# Entry point
# ─────────────────────────────────────────────
def main() -> None:
    """
    Script entry point.

    This function creates the CLI object and delegates execution to it.
    Keeping this function small makes the script easier to read and test.
    """
    ProducerCLI().run()


if __name__ == "__main__":
    main()
