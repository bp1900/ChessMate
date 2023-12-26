import chess.engine
import subprocess
import asyncio

class ChessEngine:
    def __init__(self, engine_path, time_limit=0.5):
        self.engine_path = engine_path
        self.time_limit = time_limit


    def compute_move(self, board):
        with chess.engine.SimpleEngine.popen_uci(self.engine_path, stderr=subprocess.DEVNULL) as engine:
            result = engine.play(board, chess.engine.Limit(time=self.time_limit))
            return result.move
        
    def set_time_limit(self, time_limit):
        self.time_limit = time_limit

    def analyze_board(self, board):
        with chess.engine.SimpleEngine.popen_uci(self.engine_path) as engine:
            info = engine.analyse(board, chess.engine.Limit(time=self.time_limit))
            return info["score"]
        
    async def compute_move_async(self, board):
        transport, engine = await chess.engine.popen_uci(self.engine_path)
        result = await engine.play(board, chess.engine.Limit(time=self.time_limit))
        await engine.quit()
        return result.move

    def compute_move_async(self, board):
        loop = asyncio.get_event_loop()
        return loop.run_until_complete(self.compute_move_async(board))