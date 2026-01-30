collaborations = [
    ["s0001", "s0002", "s0003"],
    ["s0002", "s0003"],
    ["s0001", "s0004"],
    ["s0003", "s0004", "s0005"],
    ["s0001", "s0002"],
    ["s0005"],
]


def get_number(collaborations_list):
    dic = {}
    for collaboration in collaborations_list:
        j = 0
        i = 1
        while j < len(collaboration):
            while i < len(collaboration):
                unique = frozenset([collaboration[j], collaboration[i]])
                if unique in dic:
                    dic[unique] += 1
                else:
                    dic[unique] = 1
                i += 1
            j += 1
            i = j + 1
    return dic

if __name__ == "__main__":
    result = get_number(collaborations)
    for pair, count in sorted(result.items(), key=lambda x: x[1], reverse=True):
        students = sorted(list(pair))
        print(f"{students[0]} & {students[1]}: {count} time(s)")