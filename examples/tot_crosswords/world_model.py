import io
from typing import NamedTuple, List, Tuple
from reasoners import WorldModel, LanguageModel
from prompts.crosswords import * 
from utils import *


crosswordsState = Tuple[MiniCrosswordsEnv, List, dict]
crosswordsAction = Tuple[str, float]


class crosswordsWorldModel(WorldModel[crosswordsState, crosswordsAction]):
    """
    crosswords World Model
    Input (x)   : a string of 4 numbers
    Output (y)  : a trajectory of 3 steps to reach 24
    State: env, actions, info (of this state)
    """

    def __init__(self,
                 base_model: LanguageModel,
                 batch_size=2,) -> None:
        super().__init__()
        self.base_model = base_model
        self.batch_size = batch_size
        self.prompt_status_cache = {}

    def init_state(self) -> list:
        ## input, output
        env = MiniCrosswordsEnv()
        env.reset(self.example)
        return (env, [], {})

    def is_terminal(self, state: crosswordsState) -> bool:
        env, actions, info = state
        if len(info) == 0:
            return False
        return True
    
    def prompt_status(self, env):
        count = {'sure': 0, 'maybe': 0, 'impossible': 0}
        for ans, data, status in zip(env.ans, env.data, env.status):
            # if status != 0: continue
            if ans.count('_') >= 4: continue
            ans = ' '.join(ans.lower())
            line = f'{data}: {ans}'
            prompt = value_prompt.format(input=line)
            if prompt in self.prompt_status_cache:
                res = self.prompt_status_cache[prompt]
            else:
                res = self.base_model.generate(prompt, temperature=0.7, num_return_sequences=1, stop=None).text[0]
                self.prompt_status_cache[prompt] = res
            # print(line)
            # print(res)
            # print()
            res = res.split('\n')[-1].strip()
            if res in count: count[res] += 1
        # print(count)
        return count

    def step(self, state: crosswordsState, action: crosswordsAction) -> crosswordsState:
        env, actions, info = state
        ## to next state
        obs, r, done, new_info = env.step(action[0])
        count = self.prompt_status(env=env)
        actions.append(action)
        print(actions)
        print(env.render_board())
        print(new_info)
        print(count)
        # info = {'total_step': len(infos), 'env_step': env.steps, 'actions': actions.copy(), 'info': info, 'count': count}
        new_info = {'env_step': env.steps, 'actions': actions.copy(), 'info': new_info, 'count': count}
        new_state = (env, actions, new_info)
        return new_state