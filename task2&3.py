collaborations = [
    ["s0001", "s0002", "s0003"],
    ["s0002", "s0003"],
    ["s0001", "s0004"],
    ["s0003", "s0004", "s0005"],
    ["s0001", "s0002"],
    ["s0005"],
]

unique_students = set()
for group in collaborations:
    for student in group:
        unique_students.add(student)

print(f"Unique Students: {unique_students}")
counts = {}

for group in collaborations:
    group.sort()
    for i in range(len(group)):
        for j in range(i + 1, len(group)):
            pair = (group[i], group[j])
            if pair in counts:
                counts[pair] += 1
            else:
                counts[pair] = 1

print("\nCollaboration Frequency:")
for pair, count in counts.items():
    print(f"{pair}: {count}")
