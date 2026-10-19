"""Deterministic appliance scheduling over half-hour power forecasts.

Power inputs are kW averages; integration returns kWh. Demo forecasts are
illustrative and independent of the Arduino experiment and rooftop APIs.
"""
import math

APPLIANCES = {
    'dishwasher': dict(name='Dishwasher', power_kw=1.2, duration_hours=2),
    'washer': dict(name='Washing machine', power_kw=0.8, duration_hours=1.5),
    'dryer': dict(name='Dryer', power_kw=2.5, duration_hours=1),
    'ev': dict(name='EV charging', power_kw=3.6, duration_hours=3),
}
STEP = 0.5


def demo_forecast():
    rows=[]
    for i in range(48):
        hour=i*STEP
        solar=round(4.5*max(0,math.sin(math.pi*(hour+0.25-7)/11)),3) if 7<=hour<18 else 0
        demand=1.4 if 17<=hour<21 else 1.1 if 7<=hour<10 else .65
        rows.append(dict(hour=hour,solar_kw=solar,home_kw=demand))
    return rows


def clock(hour):
    minutes=round(hour*60)
    if minutes==1440:return '12:00 AM (+1 day)'
    return f'{(minutes//60)%12 or 12}:{minutes%60:02d} '+('AM' if minutes<720 else 'PM')


def plan_appliance(forecast, power_kw, duration_hours, earliest, deadline):
    values=[power_kw,duration_hours,earliest,deadline]
    if not all(isinstance(v,(int,float)) and math.isfinite(v) for v in values):
        raise ValueError('Enter valid numeric settings.')
    if not .05<=power_kw<=20 or not .5<=duration_hours<=12:
        raise ValueError('Power must be 0.05–20 kW and duration 0.5–12 hours.')
    if any(abs(v/STEP-round(v/STEP))>1e-8 for v in (duration_hours,earliest,deadline)):
        raise ValueError('Use half-hour time increments.')
    if not 0<=earliest<deadline<=24:
        raise ValueError('Finish-by time must be later than the earliest start, within the same day.')
    if deadline-earliest<duration_hours:
        raise ValueError('This task cannot finish in the selected window. Choose a later deadline or shorter duration.')
    if len(forecast)!=48 or any(row['hour']!=i*STEP for i,row in enumerate(forecast)):
        raise ValueError('A complete half-hour forecast is required.')
    if any(not math.isfinite(r[k]) or r[k]<0 for r in forecast for k in ['solar_kw','home_kw']):
        raise ValueError('Forecast power values must be finite and nonnegative.')
    candidates=[]
    slots=round(duration_hours/STEP)
    for first in range(round(earliest/STEP),round((deadline-duration_hours)/STEP)+1):
        available=[max(0,r['solar_kw']-r['home_kw']) for r in forecast[first:first+slots]]
        solar=sum(min(power_kw,p)*STEP for p in available)
        energy=power_kw*duration_hours
        candidates.append(dict(start=first*STEP,end=first*STEP+duration_hours,solar_kwh=solar,grid_kwh=max(0,energy-solar)))
    # Earliest start wins ties; minimize incremental appliance grid energy.
    best=min(candidates,key=lambda c:(round(c['grid_kwh'],9),c['start']))
    baseline=candidates[0]
    return dict(**best,energy_kwh=energy,solar_percent=100*best['solar_kwh']/energy,
                avoided_grid_kwh=max(0,baseline['grid_kwh']-best['grid_kwh']),
                baseline=baseline,candidates=candidates,
                start_label=clock(best['start']),end_label=clock(best['end']),
                earliest_label=clock(earliest),deadline_label=clock(deadline))


def plan_day(forecast, tasks, allow_parallel=True):
    """Search task orders and improve schedules; solar is shared per slot.

    This bounded deterministic search provides a suggested schedule, not a
    proof of the global optimum. All selected tasks run once, uninterrupted.
    """
    from itertools import permutations
    if not 1<=len(tasks)<=4:
        raise ValueError('Choose between one and four appliances.')
    if len({t['id'] for t in tasks})!=len(tasks):
        raise ValueError('Choose each appliance only once.')
    choices={}
    for t in tasks:
        p=plan_appliance(forecast,t['power_kw'],t['duration_hours'],t['earliest'],t['deadline'])
        choices[t['id']]=[round(c['start']/STEP) for c in p['candidates']]
    available=[max(0,r['solar_kw']-r['home_kw']) for r in forecast]
    by_id={t['id']:t for t in tasks}
    ids=sorted(by_id)
    def demand(schedule):
        load=[0.0]*48
        for key,first in schedule.items():
            t=by_id[key]
            for i in range(first,first+round(t['duration_hours']/STEP)):
                load[i]+=t['power_kw']
        return load
    def score(schedule):
        return sum(max(0,p-available[i])*STEP for i,p in enumerate(demand(schedule)))
    def fits(key,first,schedule):
        if allow_parallel:return True
        end=first+round(by_id[key]['duration_hours']/STEP)
        return all(end<=start or first>=start+round(by_id[other]['duration_hours']/STEP) for other,start in schedule.items())
    best=None;best_key=None
    for order in permutations(ids):
        schedule={}
        for key in order:
            feasible=[first for first in choices[key] if fits(key,first,schedule)]
            if not feasible:break
            schedule[key]=min(feasible,key=lambda first:(round(score({**schedule,key:first}),9),first))
        if len(schedule)!=len(ids):continue
        for _ in range(3):
            before=dict(schedule)
            for key in order:
                others={k:v for k,v in schedule.items() if k!=key}
                feasible=[first for first in choices[key] if fits(key,first,others)]
                schedule[key]=min(feasible,key=lambda first:(round(score({**others,key:first}),9),first))
            if schedule==before:break
        candidate=(round(score(schedule),9),tuple(schedule[k] for k in ids))
        if best_key is None or candidate<best_key:best_key=candidate;best=dict(schedule)
    if best is None:
        raise ValueError('No schedule found within these windows. Allow parallel runs or widen the deadlines.')
    baseline={key:choices[key][0] for key in ids}
    load=demand(best)
    energy=sum(t['power_kw']*t['duration_hours'] for t in tasks)
    grid=score(best)
    rows=[]
    for key in ids:
        t=by_id[key];start=best[key]*STEP;end=start+t['duration_hours']
        rows.append(dict(**t,start=start,end=end,start_label=clock(start),end_label=clock(end),
                         left=100*start/24,width=100*t['duration_hours']/24))
    rows.sort(key=lambda r:(r['start'],r['id']))
    overlaps=any(sum(first<=i<first+round(by_id[key]['duration_hours']/STEP) for key,first in best.items())>1 for i in range(48))
    baseline_valid=allow_parallel or all(fits(k,v,{j:w for j,w in baseline.items() if j!=k}) for k,v in baseline.items())
    return dict(rows=rows,energy_kwh=energy,solar_kwh=max(0,energy-grid),grid_kwh=grid,
                solar_percent=100*max(0,energy-grid)/energy,peak_kw=max(load),has_overlap=overlaps,
                baseline_grid_kwh=score(baseline) if baseline_valid else None,
                avoided_grid_kwh=max(0,score(baseline)-grid) if baseline_valid else None,
                slots=[dict(hour=i*STEP,task_kw=p,available_kw=available[i],solar_kw=min(p,available[i]),grid_kw=max(0,p-available[i])) for i,p in enumerate(load)])
