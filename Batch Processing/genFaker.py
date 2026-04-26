import csv
import math
import copy
import random
from datetime import datetime, timedelta
from pathlib import Path
from collections import deque
from faker import Faker

# =========================================================
# CONFIGURACION GENERAL
# =========================================================
OUTPUT_DIR = "dataset_faker"
TARGET_TOTAL_GB = 30
MAX_FILE_GB = 2
BATCH_SIZE = 100_000
SEED = 42

TARGET_TOTAL_BYTES = TARGET_TOTAL_GB * 1024**3
MAX_FILE_BYTES = MAX_FILE_GB * 1024**3

random.seed(SEED)
Faker.seed(SEED)
fake = Faker("es_MX")
fake.seed_instance(SEED)

# =========================================================
# CONFIGURACION DE SUCIEDAD
# Ajusta estos valores para hacer el dataset mas o menos "roto"
# =========================================================
DIRTY_ROW_PROB = 0.45
NULL_FIELD_PROB = 0.04
OUTLIER_PROB = 0.03
EXACT_DUPLICATE_PROB = 0.02
PARTIAL_DUPLICATE_PROB = 0.04
MALFORMED_EMAIL_PROB = 0.04
BAD_PHONE_PROB = 0.04
TYPO_PROB = 0.05
WHITESPACE_NOISE_PROB = 0.05
CASE_NOISE_PROB = 0.05
DATE_CORRUPTION_PROB = 0.03
CATEGORY_NOISE_PROB = 0.03
ID_CORRUPTION_PROB = 0.01

CACHE_SIZE_FOR_DUPLICATES = 50_000

# =========================================================
# HEADERS
# =========================================================
HEADERS = [
    "id",
    "email",
    "nombre",
    "apellido_paterno",
    "apellido_materno",
    "edad",
    "sexo",
    "telefono",
    "ciudad",
    "estado",
    "pais",
    "fecha_registro",
    "ultimo_login",
    "ocupacion",
    "estado_civil",
    "nivel_estudios",
    "ingreso_mensual",
    "score_credito",
    "activo",
    "compras_12m",
    "saldo_actual",
    "segmento_cliente"
]

NULL_LIKE_VALUES = ["", "NULL", "null", "N/A", "NA", "None", "Sin dato"]

NULLABLE_FIELDS = [
    "email", "telefono", "ciudad", "estado", "pais",
    "ocupacion", "estado_civil", "nivel_estudios",
    "ingreso_mensual", "score_credito", "fecha_registro",
    "ultimo_login", "saldo_actual", "segmento_cliente"
]

TEXT_FIELDS = [
    "nombre", "apellido_paterno", "apellido_materno",
    "ciudad", "estado", "pais", "ocupacion",
    "estado_civil", "nivel_estudios"
]

# =========================================================
# CATALOGOS
# =========================================================
DOMINIOS_EMAIL = [
    ("gmail.com", 0.40),
    ("outlook.com", 0.18),
    ("hotmail.com", 0.14),
    ("yahoo.com", 0.08),
    ("empresa.com", 0.05),
    ("mail.com", 0.05),
    ("proton.me", 0.03),
    ("icloud.com", 0.04),
    ("universidad.edu", 0.03)
]

ESTADOS_CIUDADES = {
    "Jalisco": ["Guadalajara", "Zapopan", "Tlaquepaque", "Puerto Vallarta"],
    "CDMX": ["Coyoacan", "Iztapalapa", "Benito Juarez", "Miguel Hidalgo"],
    "Nuevo Leon": ["Monterrey", "San Nicolas", "Guadalupe", "Apodaca"],
    "Estado de Mexico": ["Toluca", "Naucalpan", "Ecatepec", "Tlalnepantla"],
    "Puebla": ["Puebla", "Tehuacan", "Atlixco"],
    "Queretaro": ["Queretaro", "San Juan del Rio"],
    "Guanajuato": ["Leon", "Irapuato", "Celaya"],
    "Yucatan": ["Merida", "Valladolid"],
    "Veracruz": ["Veracruz", "Xalapa", "Coatzacoalcos"],
    "Baja California": ["Tijuana", "Mexicali", "Ensenada"]
}

OCUPACIONES = [
    ("Estudiante", 0.14),
    ("Analista", 0.12),
    ("Ingeniero", 0.11),
    ("Asistente", 0.08),
    ("Gerente", 0.05),
    ("Operador", 0.10),
    ("Tecnico", 0.09),
    ("Ventas", 0.10),
    ("Marketing", 0.05),
    ("Profesor", 0.06),
    ("Medico", 0.03),
    ("Abogado", 0.03),
    ("Disenador", 0.02),
    ("Freelancer", 0.02)
]

ESTADOS_CIVILES = [
    ("Soltero", 0.42),
    ("Casado", 0.35),
    ("Divorciado", 0.08),
    ("Union libre", 0.12),
    ("Viudo", 0.03)
]

NIVELES_ESTUDIO = [
    ("Secundaria", 0.12),
    ("Preparatoria", 0.25),
    ("Tecnico", 0.14),
    ("Licenciatura", 0.34),
    ("Maestria", 0.11),
    ("Doctorado", 0.04)
]

SEGMENTOS = [
    ("Bronze", 0.45),
    ("Silver", 0.30),
    ("Gold", 0.18),
    ("Platinum", 0.07)
]

PAISES = [
    ("Mexico", 0.82),
    ("Colombia", 0.05),
    ("Argentina", 0.04),
    ("Chile", 0.03),
    ("Peru", 0.03),
    ("Espana", 0.02),
    ("USA", 0.01)
]

# =========================================================
# UTILIDADES
# =========================================================
def weighted_choice(options):
    values = [x[0] for x in options]
    weights = [x[1] for x in options]
    return random.choices(values, weights=weights, k=1)[0]

def random_date(start_date, end_date):
    delta = end_date - start_date
    total_seconds = int(delta.total_seconds())
    return start_date + timedelta(seconds=random.randint(0, total_seconds))

def clean_email_text(text):
    return (
        str(text).lower()
        .replace(" ", "")
        .replace("á", "a")
        .replace("é", "e")
        .replace("í", "i")
        .replace("ó", "o")
        .replace("ú", "u")
        .replace("ñ", "n")
    )

def random_missing_value():
    return random.choice(NULL_LIKE_VALUES)

def maybe(prob):
    return random.random() < prob

def generate_age():
    bucket = random.choices(
        ["18_24", "25_34", "35_44", "45_54", "55_70"],
        weights=[0.18, 0.34, 0.22, 0.16, 0.10],
        k=1
    )[0]

    if bucket == "18_24":
        return random.randint(18, 24)
    if bucket == "25_34":
        return random.randint(25, 34)
    if bucket == "35_44":
        return random.randint(35, 44)
    if bucket == "45_54":
        return random.randint(45, 54)
    return random.randint(55, 70)

def generate_name_and_gender():
    sexo = random.choices(["M", "F", "X"], weights=[0.495, 0.495, 0.01], k=1)[0]

    nombre = fake.first_name()
    apellido1 = fake.last_name()
    apellido2 = fake.last_name()

    while apellido2 == apellido1:
        apellido2 = fake.last_name()

    return nombre, apellido1, apellido2, sexo

def generate_location():
    estado = random.choice(list(ESTADOS_CIUDADES.keys()))
    ciudad = random.choice(ESTADOS_CIUDADES[estado])
    pais = weighted_choice(PAISES)
    return ciudad, estado, pais

def generate_phone():
    lada = random.choice(["33", "55", "81", "222", "442", "999", "229", "664"])
    numero = "".join(random.choices("0123456789", k=8))
    return f"+52{lada}{numero}"

def generate_email(nombre, apellido1, row_id):
    local_base = clean_email_text(f"{nombre}.{apellido1}.{row_id % 1000000}")

    variants = [
        local_base,
        clean_email_text(fake.user_name()),
        clean_email_text(f"{nombre}.{apellido1}{random.randint(1, 9999)}"),
        clean_email_text(f"{nombre[:1]}{apellido1}{row_id % 10000}")
    ]

    local = random.choice(variants)
    domain = weighted_choice(DOMINIOS_EMAIL)

    return f"{local}@{domain}"

def generate_income(segmento, ocupacion):
    base = {
        "Bronze": 9000,
        "Silver": 18000,
        "Gold": 35000,
        "Platinum": 70000
    }[segmento]

    factor_ocupacion = {
        "Estudiante": 0.45,
        "Asistente": 0.75,
        "Operador": 0.80,
        "Tecnico": 0.95,
        "Ventas": 1.00,
        "Analista": 1.10,
        "Ingeniero": 1.25,
        "Marketing": 1.05,
        "Profesor": 1.00,
        "Gerente": 1.80,
        "Medico": 2.20,
        "Abogado": 1.90,
        "Disenador": 0.95,
        "Freelancer": 1.15
    }.get(ocupacion, 1.0)

    ingreso = random.lognormvariate(math.log(base * factor_ocupacion), 0.35)
    ingreso = round(min(max(ingreso, 3500), 300000), 2)
    return ingreso

def generate_credit_score(ingreso, edad):
    score = 550 + (edad - 18) * 2.2 + min(ingreso / 1200, 180) + random.gauss(0, 45)
    score = max(300, min(850, int(score)))
    return score

def generate_purchase_count(segmento):
    if segmento == "Bronze":
        return max(0, int(random.lognormvariate(1.1, 0.8)))
    if segmento == "Silver":
        return max(0, int(random.lognormvariate(1.7, 0.7)))
    if segmento == "Gold":
        return max(0, int(random.lognormvariate(2.1, 0.6)))
    return max(0, int(random.lognormvariate(2.5, 0.5)))

def generate_balance(segmento, ingreso):
    factor = {
        "Bronze": 0.20,
        "Silver": 0.45,
        "Gold": 0.80,
        "Platinum": 1.40
    }[segmento]
    saldo = abs(random.gauss(ingreso * factor, ingreso * 0.30))
    saldo = round(min(saldo, 1_000_000), 2)
    return saldo

# =========================================================
# GENERACION LIMPIA
# =========================================================
def generate_clean_row(row_id):
    nombre, apellido1, apellido2, sexo = generate_name_and_gender()
    edad = generate_age()
    ciudad, estado, pais = generate_location()
    ocupacion = weighted_choice(OCUPACIONES)
    estado_civil = weighted_choice(ESTADOS_CIVILES)
    nivel_estudios = weighted_choice(NIVELES_ESTUDIO)
    segmento = weighted_choice(SEGMENTOS)

    fecha_registro = fake.date_time_between(
        start_date=datetime(2018, 1, 1),
        end_date=datetime(2026, 4, 1)
    )

    ultimo_login = fake.date_time_between(
        start_date=fecha_registro,
        end_date=datetime(2026, 4, 13)
    )

    activo = "1" if (datetime(2026, 4, 13) - ultimo_login).days <= 120 else random.choice(["0", "1"])
    telefono = generate_phone()

    ingreso_mensual = generate_income(segmento, ocupacion)
    score_credito = generate_credit_score(ingreso_mensual, edad)
    compras_12m = generate_purchase_count(segmento)
    saldo_actual = generate_balance(segmento, ingreso_mensual)

    email = generate_email(nombre, apellido1, row_id)

    return {
        "id": f"CLI{row_id:012d}",
        "email": email,
        "nombre": nombre,
        "apellido_paterno": apellido1,
        "apellido_materno": apellido2,
        "edad": edad,
        "sexo": sexo,
        "telefono": telefono,
        "ciudad": ciudad,
        "estado": estado,
        "pais": pais,
        "fecha_registro": fecha_registro.strftime("%Y-%m-%d %H:%M:%S"),
        "ultimo_login": ultimo_login.strftime("%Y-%m-%d %H:%M:%S"),
        "ocupacion": ocupacion,
        "estado_civil": estado_civil,
        "nivel_estudios": nivel_estudios,
        "ingreso_mensual": f"{ingreso_mensual:.2f}",
        "score_credito": score_credito,
        "activo": activo,
        "compras_12m": compras_12m,
        "saldo_actual": f"{saldo_actual:.2f}",
        "segmento_cliente": segmento
    }

# =========================================================
# FUNCIONES DE SUCIEDAD
# =========================================================
def mutate_typo(text):
    if not text or not isinstance(text, str) or len(text) < 3:
        return text

    option = random.choice(["drop_char", "repeat_char", "swap_char", "replace_vowel"])

    if option == "drop_char":
        pos = random.randint(0, len(text) - 1)
        return text[:pos] + text[pos + 1:]

    if option == "repeat_char":
        pos = random.randint(0, len(text) - 1)
        return text[:pos] + text[pos] + text[pos:]

    if option == "swap_char" and len(text) >= 4:
        pos = random.randint(0, len(text) - 2)
        chars = list(text)
        chars[pos], chars[pos + 1] = chars[pos + 1], chars[pos]
        return "".join(chars)

    if option == "replace_vowel":
        replacements = {"a": "e", "e": "i", "i": "o", "o": "u", "u": "a"}
        chars = list(text)
        positions = [i for i, c in enumerate(chars) if c.lower() in replacements]
        if positions:
            pos = random.choice(positions)
            original = chars[pos]
            new_c = replacements[original.lower()]
            chars[pos] = new_c.upper() if original.isupper() else new_c
            return "".join(chars)

    return text

def add_whitespace_noise(text):
    if not text or not isinstance(text, str):
        return text

    option = random.choice(["leading", "trailing", "double_internal", "all"])
    if option == "leading":
        return "  " + text
    if option == "trailing":
        return text + "   "
    if option == "double_internal":
        return text.replace(" ", "  ") if " " in text else text[:1] + "  " + text[1:]
    return " " + text + " "

def add_case_noise(text):
    if not text or not isinstance(text, str):
        return text

    option = random.choice(["upper", "lower", "title", "mixed"])
    if option == "upper":
        return text.upper()
    if option == "lower":
        return text.lower()
    if option == "title":
        return text.title()
    return "".join(c.upper() if random.random() < 0.5 else c.lower() for c in text)

def corrupt_email(email):
    if not email or "@" not in str(email):
        return email

    local, domain = email.split("@", 1)
    patterns = [
        f"{local}{domain}",
        f"{local}@@{domain}",
        f"{local}@",
        f"@{domain}",
        f"{local}@gmal.com",
        f"{local} {domain}",
        f"{local}@{domain}.mx.mx",
        f"{local}@{domain} ",
        f" {local}@{domain}",
        f"{local}@{domain.replace('.', '')}"
    ]
    return random.choice(patterns)

def corrupt_phone(phone):
    patterns = [
        "12345",
        "abcdefghij",
        "+52-33-ABC-1234",
        "000000000000000000",
        phone.replace("+", ""),
        phone + "999999",
        "(33) 1234-ABCD",
        "SIN TELEFONO",
        "",
        random_missing_value()
    ]
    return random.choice(patterns)

def corrupt_date(date_str):
    patterns = [
        "",
        random_missing_value(),
        "2026-13-45 99:99:99",
        "31/02/2025",
        "1900-01-01 00:00:00",
        "2099-12-31 23:59:59",
        "15-04-2026",
        "04/15/2026 10:22 AM",
        "ayer",
        "20260415103059"
    ]
    return random.choice(patterns)

def corrupt_category(field_name, value):
    category_map = {
        "sexo": ["Masculino", "Femenino", "fem", "M ", "?", "No binario", "NA", ""],
        "activo": ["true", "false", "SI", "NO", "1 ", " 0", "activo", "inactivo"],
        "segmento_cliente": ["bronze", "GOLD", "vip", "premium", "?", ""],
        "estado_civil": ["casad@", "solterx", "N/A", "Separado", ""],
        "nivel_estudios": ["uni", "lic", "master", "doctor", "nulo", ""]
    }
    options = category_map.get(field_name)
    if not options:
        return value
    return random.choice(options)

def inject_nulls(row):
    for field in NULLABLE_FIELDS:
        if maybe(NULL_FIELD_PROB):
            row[field] = random_missing_value()

def inject_outliers(row):
    field = random.choice(["edad", "ingreso_mensual", "score_credito", "compras_12m", "saldo_actual"])

    if field == "edad":
        row["edad"] = random.choice([-5, 0, 4, 121, 180, 999])

    elif field == "ingreso_mensual":
        row["ingreso_mensual"] = random.choice([
            "-5000.00", "0.00", "99999999.99", "1000000000", "abc", ""
        ])

    elif field == "score_credito":
        row["score_credito"] = random.choice([-10, 0, 1200, 9999, "NA", "sin_score"])

    elif field == "compras_12m":
        row["compras_12m"] = random.choice([-12, 99999, 1000000, "muchas", ""])

    elif field == "saldo_actual":
        row["saldo_actual"] = random.choice([
            "-999999.99", "999999999.99", "1e20", "desconocido", ""
        ])

def inject_text_noise(row):
    chosen_fields = random.sample(TEXT_FIELDS, k=random.randint(1, min(3, len(TEXT_FIELDS))))
    for field in chosen_fields:
        if field in row and isinstance(row[field], str):
            value = row[field]
            if maybe(TYPO_PROB):
                value = mutate_typo(value)
            if maybe(WHITESPACE_NOISE_PROB):
                value = add_whitespace_noise(value)
            if maybe(CASE_NOISE_PROB):
                value = add_case_noise(value)
            row[field] = value

def inject_category_noise(row):
    possible = ["sexo", "activo", "segmento_cliente", "estado_civil", "nivel_estudios"]
    chosen = random.choice(possible)
    row[chosen] = corrupt_category(chosen, row.get(chosen))

def inject_id_noise(row):
    patterns = [
        row["id"].replace("CLI", "cli"),
        row["id"].replace("CLI", ""),
        row["id"] + "A",
        "ID-" + row["id"],
        "",
        random_missing_value()
    ]
    row["id"] = random.choice(patterns)

def dirty_row(row):
    inject_nulls(row)

    if maybe(MALFORMED_EMAIL_PROB):
        row["email"] = corrupt_email(row.get("email"))

    if maybe(BAD_PHONE_PROB):
        row["telefono"] = corrupt_phone(row.get("telefono"))

    if maybe(DATE_CORRUPTION_PROB):
        chosen_date_field = random.choice(["fecha_registro", "ultimo_login"])
        row[chosen_date_field] = corrupt_date(row.get(chosen_date_field))

    if maybe(OUTLIER_PROB):
        inject_outliers(row)

    if maybe(CATEGORY_NOISE_PROB):
        inject_category_noise(row)

    if maybe(ID_CORRUPTION_PROB):
        inject_id_noise(row)

    inject_text_noise(row)

    return row

def make_partial_duplicate(base_row, new_id):
    row = copy.deepcopy(base_row)

    if random.random() < 0.65:
        row["id"] = f"CLI{new_id:012d}"

    candidate_fields = [
        "telefono", "email", "ciudad", "estado", "ultimo_login",
        "saldo_actual", "compras_12m", "ocupacion", "segmento_cliente"
    ]
    fields_to_mutate = random.sample(candidate_fields, k=random.randint(1, 4))

    for field in fields_to_mutate:
        if field == "telefono":
            row["telefono"] = generate_phone()
        elif field == "email":
            if row.get("nombre") and row.get("apellido_paterno"):
                row["email"] = generate_email(row["nombre"], row["apellido_paterno"], random.randint(1, 999999))
        elif field == "ciudad" or field == "estado":
            ciudad, estado, pais = generate_location()
            row["ciudad"] = ciudad
            row["estado"] = estado
            row["pais"] = pais
        elif field == "ultimo_login":
            row["ultimo_login"] = random_date(
                datetime(2024, 1, 1),
                datetime(2026, 4, 13)
            ).strftime("%Y-%m-%d %H:%M:%S")
        elif field == "saldo_actual":
            row["saldo_actual"] = f"{round(random.uniform(0, 500000), 2):.2f}"
        elif field == "compras_12m":
            row["compras_12m"] = random.randint(0, 800)
        elif field == "ocupacion":
            row["ocupacion"] = weighted_choice(OCUPACIONES)
        elif field == "segmento_cliente":
            row["segmento_cliente"] = weighted_choice(SEGMENTOS)

    if maybe(DIRTY_ROW_PROB):
        row = dirty_row(row)

    return row

def row_to_list(row):
    return [row.get(col, "") for col in HEADERS]

# =========================================================
# GENERADOR PRINCIPAL
# =========================================================
def generate_dataset():
    output_path = Path(OUTPUT_DIR)
    output_path.mkdir(parents=True, exist_ok=True)

    total_written_bytes = 0
    total_rows = 0
    file_index = 1
    global_row_id = 1

    recent_rows = deque(maxlen=CACHE_SIZE_FOR_DUPLICATES)

    while total_written_bytes < TARGET_TOTAL_BYTES:
        file_path = output_path / f"clientes_part_{file_index:02d}.csv"

        with open(file_path, mode="w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(HEADERS)
            f.flush()

            while True:
                batch_rows = []

                for _ in range(BATCH_SIZE):
                    r = random.random()

                    if recent_rows and r < EXACT_DUPLICATE_PROB:
                        row = copy.deepcopy(random.choice(recent_rows))

                    elif recent_rows and r < EXACT_DUPLICATE_PROB + PARTIAL_DUPLICATE_PROB:
                        row = make_partial_duplicate(random.choice(recent_rows), global_row_id)

                    else:
                        row = generate_clean_row(global_row_id)
                        if maybe(DIRTY_ROW_PROB):
                            row = dirty_row(row)

                    batch_rows.append(row_to_list(row))
                    recent_rows.append(copy.deepcopy(row))
                    global_row_id += 1
                    total_rows += 1

                writer.writerows(batch_rows)
                f.flush()

                current_file_size = file_path.stat().st_size
                current_total_size = total_written_bytes + current_file_size

                print(
                    f"Archivo: {file_path.name} | "
                    f"Tamaño archivo: {current_file_size / (1024**3):.2f} GB | "
                    f"Total: {current_total_size / (1024**3):.2f}/{TARGET_TOTAL_GB} GB | "
                    f"Filas: {total_rows:,}"
                )

                if current_total_size >= TARGET_TOTAL_BYTES:
                    total_written_bytes = current_total_size
                    break

                if current_file_size >= MAX_FILE_BYTES:
                    total_written_bytes += current_file_size
                    break

        file_index += 1

    print("\nProceso terminado")
    print(f"Directorio de salida: {output_path.resolve()}")
    print(f"Tamaño total aprox: {total_written_bytes / (1024**3):.2f} GB")
    print(f"Total filas generadas aprox: {total_rows:,}")

if __name__ == "__main__":
    generate_dataset()