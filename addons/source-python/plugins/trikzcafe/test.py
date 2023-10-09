from messages import SayText2
from listeners.tick import Repeat
from listeners import OnLevelEnd
from listeners import OnLevelInit
MSG = ['Example: Type "Ranking" in the chat to see your stats.']
MSG_TIMER = 0.1


@Repeat
def _msg_repeater():
    for text in MSG:
        SayText2(str(text)).send()


_msg_repeater.start(MSG_TIMER, cancel_on_level_end=True)

