from datetime import datetime
import inspect

levels = ["DEBUG", "INFO", "WARNING", "ERROR"]

color_codes = {
            levels[0]: "\033[94m",      # Blue
            levels[1]: "\033[92m",      # Green
            levels[2]: "\033[93m",      # Yellow
            levels[3]: "\033[91m"       # Red
            }
color_reset = "\033[0m"

class logger:
    debug_cnt = 0
    info_cnt = 0
    warning_cnt = 0
    error_cnt = 0

    active_log_levels = []

    def __init__(self, active_log_levels:list = ["INFO", "WARNING", "ERROR"]):
        self.active_log_levels = active_log_levels
        self.info("Logger initialized")

    def _log(self, message):
        print(f"{message}\n")

    def log(self, message, level="INFO"):
        if level not in levels:
            raise ValueError(f"Invalid log level: {level}")
        
        if level in self.active_log_levels:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            level_str = f"{color_codes[level]}[{level}]{color_reset}"
            frame = inspect.currentframe().f_back.f_back
            filename = frame.f_code.co_filename
            lineno = frame.f_lineno

            log_message = f"{timestamp} {filename}:{lineno} {level_str:<10} {message}"
            self._log(log_message)

    def debug(self, message):
        self.debug_cnt += 1
        self.log(message, "DEBUG")

    def info(self, message):
        self.info_cnt += 1
        self.log(message, "INFO")
    
    def warning(self, message):    
        self.warning_cnt += 1
        self.log(message, "WARNING")

    def error(self, message):    
        self.error_cnt += 1
        self.log(message, "ERROR")

    def summary(self):
        self._log("\n----------------------   Log summary   ----------------------")
        self._log(f"DEBUG: {self.debug_cnt}")
        self._log(f"INFO: {self.info_cnt}")
        self._log(f"WARNING: {self.warning_cnt}")
        self._log(f"ERROR: {self.error_cnt}")

        if self.error_cnt > 0:
            self._log(f"{color_codes["ERROR"]}There were errors in the log file. Please check the log file for details.{color_reset}")

log = logger(["DEBUG", "INFO", "WARNING", "ERROR"])




if __name__ == "__main__":
    log = logger()
    log.debug("To jest wiadomość debug")    
    log.info("To jest wiadomość info")
    log.warning("To jest wiadomość warning")
    log.error("To jest wiadomość error")

    log.summary()


