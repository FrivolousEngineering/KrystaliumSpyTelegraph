from typing import List


class SentenceSplitter:
    """
    Splitting text into a number of lines, attempting to keep it balanced is a *weirdly* difficult problem.
    I've found multiple ways to solve the same issue, but as is tradition, i haven't been able to find one algorithm
    that clearly outshines the others.

    """
    @staticmethod
    def findOptimalSplit(text: str, num_lines: int) -> List[str]:
        # Since I've not been able to find one algorithm that is the best, we just go for the naive solution of trying
        # them all and just selecting whatever worked best on that specific case.
        parts = []
        parts.append(SentenceSplitter.minRaggedSplit(text, num_lines))
        parts.append(SentenceSplitter.recursiveSplit(text, num_lines))
        parts.append(SentenceSplitter.simpleSplit(text, num_lines))

        for part in parts:
            # We also have a method that checks if it can improve the results by moving some words around.
            while SentenceSplitter.decreaseLargeStringParts(part):
                pass

        # We have a few simple heuristics:
        # 1. The longest line needs to be as short as possible (always trumps the rest!)
        # 2. The shortest line needs to be as long as possible.

        lengths = [SentenceSplitter._calcLengths(part) for part in parts]

        max_length = [max(l) for l in lengths]

        # Filter out the results with the lowest high values:
        shortest_max_length_indicies = SentenceSplitter._getIndexesLowestValueInList(max_length)
        filtered_parts = [parts[i] for i in shortest_max_length_indicies]

        lengths = [lengths[i] for i in shortest_max_length_indicies]
        min_length = [min(l) for l in lengths]

        longest_min_length_indicies = SentenceSplitter._getIndexesHighestValueInList(min_length)

        return filtered_parts[longest_min_length_indicies[0]]

    @staticmethod
    def _wrapMinWidth(words: List[str], n):
        r = []
        l = ""
        for word in words:
            if len(word) + len(l) > n:
                r = r + [l]
                l = ""
            l += " " if len(l) > 0 else ""
            l += word
        return r + [l]

    @staticmethod
    def recursiveSplit(text: str, num_lines: int) -> List[str]:
        words = text.split(" ")
        hi, lo = sum([len(w) for w in words]), min([len(w) for w in words])
        while lo < hi:
            mid = lo + (hi - lo) / 2
            v = SentenceSplitter._wrapMinWidth(words, mid)
            if len(v) > num_lines:
                lo = mid + 1
            elif len(v) <= num_lines:
                hi = mid
        return SentenceSplitter._wrapMinWidth(words, lo)

    @staticmethod
    def minRaggedSplit(text, num_lines: int) -> List[str]:
        P = 2
        words = text.split()
        cumulative_word_width = [0]
        for word in words:
            cumulative_word_width.append(cumulative_word_width[-1] + len(word))
        total_width = cumulative_word_width[-1] + len(words) - 1  # len(words) - 1 spaces
        line_width = float(total_width - (num_lines - 1)) / float(num_lines)  # n - 1 line breaks

        def cost(i, j):
            """
            cost of a line words[i], ..., words[j - 1] (words[i:j])
            """
            actual_line_width = max(j - i - 1, 0) + (cumulative_word_width[j] - cumulative_word_width[i])
            return (line_width - actual_line_width) ** P

        total_costs = {}  # Total cost function

        for stage in range(num_lines):
            if stage == 0:
                total_costs[stage] = []
                i = 0
                for j in range(i, len(words) + 1):
                    total_costs[stage].append([cost(i, j), 0])
            elif stage == num_lines - 1:
                total_costs[stage] = [[float('inf'), 0] for i in range(len(words) + 1)]
                for i in range(len(words) + 1):
                    j = len(words)
                    if total_costs[stage - 1][i][0] + cost(i, j) < total_costs[stage][j][0]:  # calculating min cost (cf f formula)
                        total_costs[stage][j][0] = total_costs[stage - 1][i][0] + cost(i, j)
                        total_costs[stage][j][1] = i

            else:
                total_costs[stage] = [[float('inf'), 0] for i in range(len(words) + 1)]
                for i in range(len(words) + 1):
                    for j in range(i, len(words) + 1):
                        if total_costs[stage - 1][i][0] + cost(i, j) < total_costs[stage][j][0]:
                            total_costs[stage][j][0] = total_costs[stage - 1][i][0] + cost(i, j)
                            total_costs[stage][j][1] = i
        result = []
        a = len(words)
        for k in range(num_lines - 1, 0, -1):  # reverse loop from n-1 to 1
            result.append(' '.join(words[total_costs[k][a][1]:a]))
            a = total_costs[k][a][1]
        result.append(' '.join(words[0:a]))
        result.reverse()

        return result

    @staticmethod
    def simpleSplit(sentence: str, num_parts: int) -> List[str]:
        words = sentence.split()
        total_words = len(words)

        if num_parts > total_words:
            raise ValueError("Number of parts cannot be greater than the number of words in the sentence.")

        words_per_part = total_words // num_parts
        remainder = total_words % num_parts

        parts: List[str] = []
        start_idx = 0

        for i in range(num_parts):
            end_idx = start_idx + words_per_part + (1 if i < remainder else 0)
            parts.append(" ".join(words[start_idx:end_idx]))
            start_idx = end_idx

        return parts

    @staticmethod
    def _getIndexesHighestValueInList(data: List) -> List[int]:
        highest_index = 0
        highest_value = 0
        for i, item in enumerate(data):
            if item > highest_value:
                highest_value = item
                highest_index = i
            elif item == highest_value:
                if type(highest_index) != list:
                    highest_index = [highest_index]
                highest_index.append(i)
        if type(highest_index) != list:
            return [highest_index]
        return highest_index

    @staticmethod
    def _getIndexesLowestValueInList(data: List) -> List[int]:
        lowest_index = 0
        lowest_value = float('inf')
        for i, item in enumerate(data):
            if item < lowest_value:
                lowest_value = item
                lowest_index = i
            elif item == lowest_value:
                if type(lowest_index) != list:
                    lowest_index = [lowest_index]
                lowest_index.append(i)
        if type(lowest_index) != list:
            return [lowest_index]
        return lowest_index

    @staticmethod
    def _calcLengths(parts: List[str]) -> List[int]:
        return [len(part) for part in parts]

    @staticmethod
    def decreaseLargeStringParts(parts: List[str]) -> bool:
        """
        Accept a list of strings. It attempts to move words from the largest of these to its neighbors. It will respect
        word boundaries. Note that it makes the changes in place. It returns true if it was able to optimize.
        """
        lengths = SentenceSplitter._calcLengths(parts)

        highest_index_list = SentenceSplitter._getIndexesHighestValueInList(lengths)
        could_optimize = False

        for highest_index in highest_index_list:
            lengths = SentenceSplitter._calcLengths(parts)
            words_to_consider = parts[highest_index].split(" ")

            move_word_front_score = 0
            move_word_back_score = 0

            # Check if we can move the first word
            if highest_index > 0:
                modified_length = len(words_to_consider[0]) + lengths[highest_index - 1] + 1
                if modified_length < lengths[highest_index]:
                    move_word_back_score = modified_length
            if highest_index + 1 < len(parts):
                modified_length = len(words_to_consider[-1]) + lengths[highest_index + 1] + 1
                if modified_length < lengths[highest_index]:
                    move_word_front_score = modified_length
            if move_word_front_score == 0 and move_word_back_score == 0:
                continue  # Nothing to do

            if move_word_front_score == 0:
                direction_to_move = "back"

            elif move_word_back_score == 0:
                direction_to_move = "front"
            else:
                direction_to_move = "front" if move_word_front_score < move_word_front_score else "back"

            if direction_to_move == "front":
                parts[highest_index] = parts[highest_index][:-len(words_to_consider[-1])].strip()
                parts[highest_index + 1] = words_to_consider[-1] + " " + parts[highest_index + 1]
            else:
                parts[highest_index] = parts[highest_index][len(words_to_consider[0]):].strip()
                parts[highest_index - 1] += " " + words_to_consider[0]

            could_optimize = move_word_back_score != 0 or move_word_front_score != 0 or could_optimize
        return could_optimize
