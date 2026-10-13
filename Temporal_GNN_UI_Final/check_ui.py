"""Exercise all six presentation pages against the existing local artifacts."""
from pathlib import Path
import time
from streamlit.testing.v1 import AppTest
from project_data import ProjectData
from intelligence.config import ARTIFACT_DIR

ROOT=Path(__file__).resolve().parent
data=ProjectData(ARTIFACT_DIR)
app=AppTest.from_file(str(ROOT/'app_intelligence.py'),default_timeout=120).run()


def clean(label):
    assert not app.exception,[str(x.value) for x in app.exception]
    assert not app.error,[str(x.value) for x in app.error]
    print('PASS:',label,flush=True)


clean('Command Center')
app.slider(key='scrub_period').set_value(49).run()
clean('Replay cursor')
cards={m.label:m.value for m in app.metric}
assert cards['Transactions replayed']==f"{data.summary['test_transactions']:,}"
assert cards['High-risk transactions']==f"{data.summary['high_score_test_transactions']:,}"
assert cards['Escalation flags']==str(data.summary['test_warning_periods'])
for page in ['Transaction Intelligence','Temporal Risk','Early Warning Center',
             'Network Investigation','Model Intelligence']:
    app.radio(key='navigation').set_value(page).run()
    clean(page)
    if page=='Transaction Intelligence':
        app.button(key='analyze').click().run(timeout=120)
        clean('Fresh GCN + GRU inference')
        assert app.session_state['inference']['difference']<1e-5
    if page=='Early Warning Center':
        assert app.session_state['alert_list']==[]
        app.checkbox(key='explore').check().run()
        app.slider(key='explore_level').set_value(0.0).run()
        app.slider(key='explore_increase').set_value(0.0).run()
        clean('Exploratory rules')
        assert app.session_state['alert_list']==[]
app.button(key='reset').click().run()
assert app.session_state['replay']['period']==42
app.button(key='start').click().run()
state=dict(app.session_state['replay']);state['last_tick']=time.monotonic()-20
app.session_state['replay']=state
app.run()
clean('Replay timer')
assert app.session_state['replay']['period']==43
app.button(key='pause').click().run()
assert not app.session_state['replay']['running']
print('ALL UI CHECKS PASSED',flush=True)
