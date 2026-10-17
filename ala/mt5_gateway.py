"""Optional MetaTrader 5 gateway with strict demo-first controls.

Requires the official MetaTrader5 Python package and a logged-in desktop terminal.
This module does not store broker passwords. The terminal/session is managed by the user.
"""
from __future__ import annotations
import os, math
from dataclasses import dataclass

LIVE_CONFIRMATION = "I UNDERSTAND REAL MONEY RISK"
MAX_RISK_PERCENT = 0.25
MAX_DAILY_LOSS_PERCENT = 1.0

class MT5SafetyError(RuntimeError): pass

@dataclass
class TradeResult:
    accepted: bool
    mode: str
    symbol: str
    side: str
    volume: float
    entry: float
    stop_loss: float
    take_profit: float
    retcode: int | None
    message: str
    order_id: int | None = None
    def to_dict(self): return self.__dict__.copy()

class MT5Gateway:
    def __init__(self, mode: str = "demo", confirmation: str | None = None):
        if mode not in {"demo", "live"}: raise ValueError("mode must be demo or live")
        self.mode=mode
        self.mt5=None
        if mode == "live":
            if os.getenv("ALA_ENABLE_LIVE_TRADING", "") != "YES_I_ACCEPT_RISK":
                raise MT5SafetyError("Live trading disabled. Set ALA_ENABLE_LIVE_TRADING=YES_I_ACCEPT_RISK only after independent review.")
            if confirmation != LIVE_CONFIRMATION:
                raise MT5SafetyError(f"Live order requires --confirm-live '{LIVE_CONFIRMATION}'.")
        try:
            import MetaTrader5 as mt5
        except ImportError as exc:
            raise RuntimeError("MetaTrader5 package missing. Install it in Windows with: py -m pip install MetaTrader5; MT5 Python integration is Windows-only.") from exc
        self.mt5=mt5
        if not mt5.initialize():
            raise RuntimeError(f"MT5 initialize failed: {mt5.last_error()}")
        self.account=mt5.account_info()
        if self.account is None:
            mt5.shutdown(); raise RuntimeError("No MT5 account session found. Log in to the terminal first.")
        baseline_raw=os.getenv("ALA_DAILY_START_EQUITY")
        if mode=="live" and not baseline_raw:
            mt5.shutdown(); raise MT5SafetyError("Live mode requires ALA_DAILY_START_EQUITY set to the verified account equity at the start of the trading day.")
        self.daily_start_equity=float(baseline_raw) if baseline_raw else float(self.account.equity)
        if not math.isfinite(self.daily_start_equity) or self.daily_start_equity<=0:
            mt5.shutdown(); raise MT5SafetyError("Daily starting equity must be a positive finite number")
        real_mode=getattr(mt5,"ACCOUNT_TRADE_MODE_REAL",2)
        demo_mode=getattr(mt5,"ACCOUNT_TRADE_MODE_DEMO",0)
        if mode=="demo" and int(self.account.trade_mode)==real_mode:
            mt5.shutdown(); raise MT5SafetyError("Refusing: MT5 terminal is logged into a REAL account; demo mode requires a demo account.")
        if mode=="live" and int(self.account.trade_mode)!=real_mode:
            mt5.shutdown(); raise MT5SafetyError("Live mode requested, but the connected account is not a real account. Refusing order.")
        if not bool(getattr(self.account,"trade_allowed",False)) or not bool(getattr(self.account,"trade_expert",False)):
            mt5.shutdown(); raise MT5SafetyError("Account/terminal does not permit automated trading.")

    def status(self) -> dict:
        refreshed=self.mt5.account_info()
        if refreshed is None: raise RuntimeError("Could not refresh MT5 account information")
        self.account=refreshed
        a=self.account
        return {"mode":self.mode,"login":int(a.login),"server":str(a.server),"company":str(a.company),"currency":str(a.currency),"balance":float(a.balance),"equity":float(a.equity),"margin_free":float(a.margin_free),"trade_mode":int(a.trade_mode),"warning":"Never share account login details or passwords."}

    def rates(self, symbol: str, timeframe: str="M15", count: int=150) -> list[dict]:
        mt5=self.mt5
        tfmap={"M1":mt5.TIMEFRAME_M1,"M5":mt5.TIMEFRAME_M5,"M15":mt5.TIMEFRAME_M15,"M30":mt5.TIMEFRAME_M30,"H1":mt5.TIMEFRAME_H1,"H4":mt5.TIMEFRAME_H4,"D1":mt5.TIMEFRAME_D1}
        if timeframe not in tfmap: raise ValueError("Unsupported timeframe; use M1, M5, M15, M30, H1, H4, D1")
        if not mt5.symbol_select(symbol,True): raise RuntimeError(f"Could not select {symbol}: {mt5.last_error()}")
        raw=mt5.copy_rates_from_pos(symbol,tfmap[timeframe],1,count) # shift=1 excludes currently forming candle
        if raw is None or len(raw)<100: raise RuntimeError(f"Not enough closed candles for {symbol}; MT5 returned {0 if raw is None else len(raw)}")
        from datetime import datetime, timezone
        return [{"timestamp":datetime.fromtimestamp(int(r["time"]),tz=timezone.utc).isoformat(),"open":float(r["open"]),"high":float(r["high"]),"low":float(r["low"]),"close":float(r["close"]),"volume":float(r["tick_volume"])} for r in raw]

    def execute_market_order(self, symbol: str, side: str, risk_percent: float=0.25, sl_points: int=300, tp_points: int=600) -> TradeResult:
        mt5=self.mt5
        refreshed=mt5.account_info()
        if refreshed is None: raise RuntimeError("Could not refresh MT5 account information; order blocked")
        self.account=refreshed
        side=side.lower()
        if side not in {"buy","sell"}: raise ValueError("side must be buy or sell")
        if not (0 < risk_percent <= MAX_RISK_PERCENT): raise MT5SafetyError(f"risk_percent must be >0 and <= {MAX_RISK_PERCENT}%")
        if not (10 <= sl_points <= 10000 and sl_points < tp_points <= 20000): raise MT5SafetyError("Require SL 10..10000 points and TP greater than SL, <=20000 points")
        # A conservative daily loss guard. The process baseline is stored in an environment variable
        # by the caller; if absent, this trade is refused rather than silently resetting the baseline.
        baseline=float(self.daily_start_equity)
        if float(self.account.equity) <= baseline*(1-MAX_DAILY_LOSS_PERCENT/100): raise MT5SafetyError("Daily loss limit reached; orders blocked")
        info=mt5.symbol_info(symbol); tick=mt5.symbol_info_tick(symbol)
        if info is None or tick is None: raise RuntimeError(f"No symbol/tick data for {symbol}")
        if not info.visible and not mt5.symbol_select(symbol,True): raise RuntimeError(f"Could not make {symbol} visible")
        point=float(info.point); digits=int(info.digits)
        entry=float(tick.ask if side=="buy" else tick.bid)
        sl=entry-(sl_points*point if side=="buy" else -sl_points*point)
        tp=entry+(tp_points*point if side=="buy" else -tp_points*point)
        sl=round(sl,digits); tp=round(tp,digits)
        tick_size=float(info.trade_tick_size or info.point); tick_value=float(info.trade_tick_value or 0)
        if tick_size<=0 or tick_value<=0: raise MT5SafetyError("Broker did not provide valid tick size/value; cannot size position safely")
        risk_cash=float(self.account.equity)*(risk_percent/100.0)
        loss_per_lot=(abs(entry-sl)/tick_size)*tick_value
        if loss_per_lot<=0 or not math.isfinite(loss_per_lot): raise MT5SafetyError("Cannot calculate stop-loss risk per lot")
        raw_volume=risk_cash/loss_per_lot
        step=float(info.volume_step); vmin=float(info.volume_min); vmax=min(float(info.volume_max),1.0)
        volume=math.floor(raw_volume/step)*step
        volume=round(volume,8)
        if volume<vmin: raise MT5SafetyError(f"Risk-based volume {volume} is below broker minimum {vmin}; no order sent")
        if volume>vmax: volume=vmax
        if not (sl < entry < tp if side=="buy" else tp < entry < sl): raise MT5SafetyError("Invalid SL/TP orientation")
        order_type=mt5.ORDER_TYPE_BUY if side=="buy" else mt5.ORDER_TYPE_SELL
        request={"action":mt5.TRADE_ACTION_DEAL,"symbol":symbol,"volume":volume,"type":order_type,"price":entry,"sl":sl,"tp":tp,"deviation":20,"magic":610181,"comment":"GoldMind ALA guarded order","type_time":mt5.ORDER_TIME_GTC,"type_filling":info.filling_mode}
        check=mt5.order_check(request)
        if check is None or int(getattr(check,"retcode",-1)) not in (0,mt5.TRADE_RETCODE_DONE):
            raise MT5SafetyError(f"Broker order_check did not approve order: {check}; no order sent")
        result=mt5.order_send(request)
        if result is None: raise RuntimeError(f"order_send returned None: {mt5.last_error()}")
        success=int(result.retcode) in (mt5.TRADE_RETCODE_DONE, getattr(mt5,"TRADE_RETCODE_PLACED",10008))
        return TradeResult(success,self.mode,symbol,side,volume,entry,sl,tp,int(result.retcode),str(result.comment),int(result.order) if result.order else None)

    def close_ala_positions(self, symbol: str) -> list[dict]:
        """Close only positions opened with this agent's magic number; never touches manual/other-bot positions."""
        mt5=self.mt5
        positions=mt5.positions_get(symbol=symbol)
        if positions is None: raise RuntimeError(f"positions_get failed: {mt5.last_error()}")
        results=[]
        for pos in positions:
            if int(getattr(pos,"magic",0)) != 610181: continue
            tick=mt5.symbol_info_tick(symbol)
            if tick is None: continue
            is_buy=int(pos.type)==int(mt5.POSITION_TYPE_BUY)
            request={"action":mt5.TRADE_ACTION_DEAL,"symbol":symbol,"volume":float(pos.volume),"type":mt5.ORDER_TYPE_SELL if is_buy else mt5.ORDER_TYPE_BUY,"position":int(pos.ticket),"price":float(tick.bid if is_buy else tick.ask),"deviation":20,"magic":610181,"comment":"GoldMind ALA signal exit","type_time":mt5.ORDER_TIME_GTC,"type_filling":mt5.symbol_info(symbol).filling_mode}
            check=mt5.order_check(request)
            if check is None or int(getattr(check,"retcode",-1)) not in (0,mt5.TRADE_RETCODE_DONE):
                results.append({"ticket":int(pos.ticket),"closed":False,"reason":str(check)}); continue
            result=mt5.order_send(request)
            results.append({"ticket":int(pos.ticket),"closed":bool(result and int(result.retcode)==mt5.TRADE_RETCODE_DONE),"retcode":int(result.retcode) if result else None})
        return results

    def positions(self, symbol: str) -> list[dict]:
        raw=self.mt5.positions_get(symbol=symbol)
        if raw is None: raise RuntimeError(f"positions_get failed: {self.mt5.last_error()}")
        return [{"ticket":int(p.ticket),"symbol":str(p.symbol),"type":int(p.type),"volume":float(p.volume),"magic":int(p.magic),"profit":float(p.profit)} for p in raw]

    def close(self):
        if self.mt5 is not None: self.mt5.shutdown()
