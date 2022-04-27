import threading

time_after_removing_sessions = 60 * 3   # seconds

class Sessions:
    
    def __init__(self):
        self.sessions = {}
        self.to_remove = {}
        self.last_id = 0
    
    def get_id(self):
        self.last_id += 1
        return self.last_id
    
    def add_new_session(self, interpreter, username, password):
        s_id = self.get_id()
        self.sessions[s_id] = {
                'interpreter': interpreter,
                'username': username,
                'password': password
            }
        
        self.set_timer_to_remove(s_id)
        
        return s_id
        
    
    def verify(self, s_id, username, password):
        if s_id is None:
            return False
        
        s_id = int(s_id)
        if s_id not in self.sessions.keys():
            return False
        
        session = self.sessions[s_id]
        if session['username'] == username and session['password'] == password:
            self.set_timer_to_remove(s_id)
            return session['interpreter']
        
        return False
    
    def set_timer_to_remove (self, s_id):
        if s_id in self.to_remove.keys():
            self.to_remove[s_id].cancel()
        
        timer = threading.Timer(time_after_removing_sessions, self.remove_session, [s_id])
        timer.start()
        self.to_remove[s_id] = timer
    
    def remove_session(self, s_id):
        
        del self.sessions[s_id]
        del self.to_remove[s_id]
