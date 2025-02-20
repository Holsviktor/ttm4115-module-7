import paho.mqtt.client as mqtt
import time
from stmpy import Machine, Driver

class Quizmaster:

    transition_list = [
             {                          'source':'initial',     'target':'s_waiting', 'effect':'on_init; start_timer("timeout", 20_000)'}
            ,{'trigger':'buzz',         'source':'s_waiting',   'target':'s_buzzed',  'effect':'on_buzz; start_timer("answer_timer", 5000)'}
            ,{'trigger':'timeout',      'source':'s_waiting',   'target':'s_waiting', 'effect':'on_timeout; start_timer("timeout", 20_000)'}
            ,{'trigger':'buzz',         'source':'s_buzzed',    'target':'s_buzzed',  'effect':'on_buzz'}
            ,{'trigger':'timeout',      'source':'s_buzzed',    'target':'s_buzzed',  'effect':''}
            ,{'trigger':'answer_timer', 'source':'s_buzzed',    'target':'s_waiting', 'effect':'answer_done; start_timer("timeout", 20_000)'}]

    state_list = [
            {'name' : 's_waiting',   'entry' : 'ask_question'}
    ]
    def __init__(self, driver, client):
        self.driver = driver
        self.answerlist = []

        self.client = client
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        self.client.connect("mqtt20.item.ntnu.no", 1883, 60)
        self.client.loop_start()

        stm_quiz = Machine(transitions=Quizmaster.transition_list, states=Quizmaster.state_list, obj=self, name='stm_quizmaster')
        self.stm = stm_quiz
        self.driver.add_machine(self.stm)

    def on_connect(self,client, userdata, flags, rc, properties):
        print(f"Connected with result code {rc}")
        client.subscribe("10/buzzers/#")

    def on_message(self, client, userdata, msg):
        print(f"[{msg.topic}] -> {msg.payload.decode('utf-8')}")
        self.answerlist.append(msg.payload.decode('utf-8'))
        self.driver.send("buzz", self.stm.id)

    def on_init(self):
        print('Quizmaster spawned')

    def on_buzz(self):
        print(f'{self.answerlist[-1]} buzzed: {self.answerlist[0]} to answer.')

    def on_timeout(self):
        print('No answers given...')

    def answer_done(self):
        print("Time's up! Next question: ")
        self.answerlist = []
        self.client.publish('10/quiz', 'reset')

    def ask_question(self):
        print("What's up with birds?")


try:
    if __name__ == "__main__":
        driver = Driver()
        client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
        quizmaster = Quizmaster(driver, client)

        driver.start()
        driver.wait_until_finished()
except KeyboardInterrupt:
    print("\rKeyboardInterrupt received, shutting down...")
    client.loop_stop()
    client.disconnect()
    print("Bye bye!\a")


