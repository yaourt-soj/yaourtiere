class MessageSplitter:
    def __init__(self, message):
        self.__input = message
        self.__character_limit = 2000
        self.__split_order = ['\n\n', '\n', '. ', '... ', '! ', '? ', ' ']
        self.__output = []
        self.__respect_limit(self.__input, 0)

    def __respect_limit(self, text, split_index):
        split_sequence = self.__split_order[split_index]
        text_split = text.split(split_sequence)
        while text_split:
            if len(text_split[0]) == 0:
                pass
            else:
                suffix = split_sequence if len(text_split) > 1 else ''
                current_text_block = text_split[0] + suffix
                if len(current_text_block) <= self.__character_limit:
                    if len(self.__output) == 0:
                        self.__output.append(current_text_block)
                    elif len(self.__output[-1] + current_text_block) <= self.__character_limit:
                        self.__output[-1] += current_text_block
                    else:
                        self.__output.append(current_text_block)
                elif split_index + 1 < len(self.__split_order):
                    self.__respect_limit(current_text_block, split_index + 1)
                else:
                    self.__split_arbitrarily(current_text_block)
            text_split.remove(text_split[0])

    def __split_arbitrarily(self, text):
        while text:
            self.__output.append(text[:self.__character_limit])
            text = text[self.__character_limit:]

    def get_message_split(self):
        return self.__output
