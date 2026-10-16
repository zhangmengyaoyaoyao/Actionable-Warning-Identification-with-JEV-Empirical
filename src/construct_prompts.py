from prompts import zero_shot, one_shot, few_shot, general_info, expertise, chain_of_thought, critique, self_heuristic


class Constructor():
    def __init__(self):
        self.warning = ''

    def setWarning(self, warningNow):
        self.warning = '# warning\n' + warningNow

    def setGeneralInfo(self, toolNow, projectNow):
        general_info.setGeneralInfo(toolNow, projectNow)

    def construct(self, prompts_technique):
        builders = {
            "zero_shot": self.construct_zero_shot,
            "one_shot": self.construct_one_shot,
            "few_shot": self.construct_few_shot,
            "general_info": self.construct_general_info,
            "expertise": self.construct_expertise,
            "chain_of_thought": self.construct_chain,
            "critique": self.construct_critique,
            "self_heuristic": self.construct_heuristic,
        }
        builder = builders.get(prompts_technique)
        if builder is None:
            raise ValueError("fail to find this prompts_technique:" + prompts_technique)
        return builder()

    def construct_zero_shot(self):
        messages = []

        user_message = zero_shot.zero_shot_prompt_USER + self.warning
        messages.append({'role': 'user', 'content': user_message})
        #test
        #print("input_zero_shot:" + user_message)

        return messages

    def construct_general_info(self):
        messages = []

        messages.append({'role': 'system', 'content': general_info.general_info_system})

        user_message = zero_shot.zero_shot_prompt_USER + self.warning
        messages.append({'role': 'user', 'content': user_message})

        return messages

    def construct_expertise(self):
        messages = []

        messages.append({'role': 'system', 'content': general_info.general_info_system})

        user_message = zero_shot.zero_shot_prompt_USER + expertise.expertise_expertise + self.warning
        messages.append({'role': 'user', 'content': user_message})
        print("exper")

        return messages

    def construct_chain(self):
        messages = []

        user_message = chain_of_thought.chain_prompt_USER + self.warning
        messages.append({'role': 'user', 'content': user_message})
        #test
        print("con COT")

        return messages

    def construct_critique(self):
        messages1 = []
        user_message = zero_shot.zero_shot_prompt_USER + self.warning
        messages1.append({'role': 'user', 'content': user_message})

        messages2 = []
        user_message = critique.critique_USER1
        messages2.append({'role': 'user', 'content': user_message})

        messages3 = []
        user_message = critique.critique_USER2
        messages3.append({'role': 'user', 'content': user_message})
        return messages1, messages2, messages3

    def construct_one_shot(self):
        raise NotImplementedError

    def construct_few_shot(self):
        raise NotImplementedError

    def construct_heuristic(self):
        raise NotImplementedError


class Java_Constructor(Constructor):
    def construct_one_shot(self):
        messages = []

        user_message = one_shot.one_shot_prompt_USER1 + one_shot.one_shot_example_java + one_shot.one_shot_prompt_USER2 + self.warning
        messages.append({'role': 'user', 'content': user_message})
        #test
        #print("input_one_shot:" + user_message)

        return messages

    def construct_few_shot(self):
        messages = []

        user_message = zero_shot.zero_shot_prompt_USER + few_shot.few_shot_example_java1 + few_shot.few_shot_example_java2 + few_shot.few_shot_example_java3 + few_shot.few_shot_example_java4 + self.warning
        messages.append({'role': 'user', 'content': user_message})

        return messages

    def construct_heuristic(self):
        messages1 = []
        messages1.append({'role': 'system', 'content': general_info.general_info_system})
        user_message = self_heuristic.heuristic_USER1 + few_shot.few_shot_example_java1 + few_shot.few_shot_example_java2 + few_shot.few_shot_example_java3 + few_shot.few_shot_example_java4
        messages1.append({'role': 'user', 'content': user_message})

        messages2 = []
        user_message = self_heuristic.heuristic_USER2 + self.warning
        messages2.append({'role': 'user', 'content': user_message})

        return messages1, messages2


class C_Constructor(Constructor):
    def construct_one_shot(self):
        messages = []

        user_message = one_shot.one_shot_prompt_USER1 + one_shot.one_shot_example_c + one_shot.one_shot_prompt_USER2 + self.warning
        messages.append({'role': 'user', 'content': user_message})
        #test
        # print("input_one_shot:" + user_message)

        return messages

    def construct_few_shot(self):
        messages = []

        user_message = zero_shot.zero_shot_prompt_USER + few_shot.few_shot_example_c1 + few_shot.few_shot_example_c2 + few_shot.few_shot_example_c3 + few_shot.few_shot_example_c4 + self.warning
        messages.append({'role': 'user', 'content': user_message})

        return messages

    def construct_heuristic(self):
        messages1 = []
        messages1.append({'role': 'system', 'content': general_info.general_info_system})
        user_message = self_heuristic.heuristic_USER1 + few_shot.few_shot_example_c1 + few_shot.few_shot_example_c2 + few_shot.few_shot_example_c3 + few_shot.few_shot_example_c4
        messages1.append({'role': 'user', 'content': user_message})

        messages2 = []
        user_message = self_heuristic.heuristic_USER2 + self.warning
        messages2.append({'role': 'user', 'content': user_message})

        return messages1, messages2
