import queue
import threading
import time


class MessageQueue(threading.Thread):
    def __init__(self, autostart=True):
        super().__init__()
        self.queue = queue.Queue()
        self.limit_msgs_to_one_in_sec = 1
        self.limit_msgs_to_one_in_min = 5
        self.limit_msgs_to_all_in_sec = 30

        self.clients = {}

        self.daemon = False
        if autostart:
            super().start()

    def run(self):
        warning = False
        while True:
            if not self.queue.empty():
                item = self.queue.get()
                bot, chat_id, text, args, kwargs = item
                now = time.time()
                if chat_id not in self.clients:
                    self.clients[chat_id] = {
                        'warning': False,
                        'times': [now],
                    }
                    bot.send_message(chat_id, text, *args, **kwargs)
                    continue

                times = self.clients[chat_id]['times']
                self.clear_times(chat_id, now)
                if len(times) < self.limit_msgs_to_one_in_min:
                    if now - times[-1] > self.limit_msgs_to_one_in_sec:
                        times.append(now)
                        bot.send_message(chat_id, text, *args, **kwargs)
                        if len(times) == self.limit_msgs_to_one_in_min:
                            self.clients[chat_id]['warning'] = True
                else:
                    print('limit')
                    if self.clients[chat_id]['warning']:
                        bot.send_message(chat_id, 'Извините, но вы превысили лимит'
                            ' запросов в минуту. Повторите свой запрос позже')
                        self.clients[chat_id]['warning'] = False
                print(len(times))
            else:
                self.clear_clients()
            time.sleep(0.1)

    def clear_clients(self):
        for_delete = []
        for chat_id in self.clients:
            self.clear_times(chat_id)
            if not self.clients[chat_id]['times']:
                for_delete.append(chat_id)
        for chat_id in for_delete:
            del self.clients[chat_id]
            print('delete', chat_id)

    def clear_times(self, chat_id, now=None, time_in_sec=60):
        times = self.clients[chat_id]['times']
        now = now or time.time()
        for t in times:
            if now - t > time_in_sec:
                times.pop(0)
            else:
                break
    
    def stop(self):
        self.queue.put(None)
        super().join()

    def send(self, bot, chat_id, text, *args, **kwargs):
        if self.is_alive():
            self.queue.put((bot, chat_id, text, args, kwargs))
    

    