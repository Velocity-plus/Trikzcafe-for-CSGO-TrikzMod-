from messages import SayText2
from listeners.tick import Repeat
from listeners import OnLevelInit
from random import choice
MSG = ['Example: Type "Ranking" in the chat to see your stats.',
       'other message #green colors..']
MSG_INTERVAL = 120


@Repeat
def _msg_repeater():
    rng_choice = choice(MSG)
    SayText2(str(rng_choice)).send()


def msg_repeater_start():
    _msg_repeater.cancel_on_level_end = True
    _msg_repeater.start(MSG_INTERVAL)


@OnLevelInit
def _on_level_start(_):
    msg_repeater_start()


msg_repeater_start()