"""New presentation entry point. Existing app.py and inference modules remain unchanged."""
import time
import streamlit as st
from project_data import ProjectData, InferenceEngine, REQUIRED
from intelligence.config import ARTIFACT_DIR, PAGES, CRITICAL_SCORE, LOW_FRACTION_OF_DECISION
from intelligence.data_adapter import DataAdapter
from intelligence.monitoring import initial_state, control, advance
from intelligence.theme import apply_theme
from intelligence import views

st.set_page_config(page_title='Temporal | Transaction Risk Intelligence',page_icon='◈',layout='wide',initial_sidebar_state='expanded')


@st.cache_resource
def load_data(path):
    return DataAdapter(ProjectData(path))


@st.cache_resource
def load_engine(path):
    return InferenceEngine(load_data(path).project)


def replay_action(action):
    st.session_state.replay=control(st.session_state.replay,action,time.monotonic())


def scrub():
    st.session_state.replay.update(period=int(st.session_state.scrub_period),running=False,
                                  last_tick=None,updated='Manual selection')


def speed_changed():
    st.session_state.replay['last_tick']=time.monotonic()


def main():
    apply_theme()
    missing=[name for name in REQUIRED if not (ARTIFACT_DIR/name).is_file()]
    if missing:
        st.title('Connect your trained intelligence')
        st.info('Place this upgrade beside the existing app.py, model.py and project_data.py. Keep the complete Kaggle export in the existing artifacts folder.')
        with st.expander('Artifact location and missing files'):
            st.code(str(ARTIFACT_DIR));st.write(missing)
        st.stop()
    try:
        with st.spinner('Verifying the saved experiment…'):
            a=load_data(str(ARTIFACT_DIR))
    except Exception as exc:
        st.error('The saved experiment could not be verified. Restore the unchanged Phase 5 export and run verify_artifacts.py.')
        with st.expander('Technical error details'):st.code(str(exc))
        st.stop()
    defaults={'replay':initial_state(),'explore':False,
              'explore_level':float(a.rule['risk_threshold'])*100,
              'explore_increase':float(a.rule['escalation_threshold'])*100,'alert_list':[]}
    for key,value in defaults.items():
        if key not in st.session_state:st.session_state[key]=value
    # Sync before creating the widget; the timer changes only the separate replay object.
    st.session_state.scrub_period=st.session_state.replay['period']
    with st.sidebar:
        st.markdown('<div class="brand">◈ TEMPORAL<small>RISK INTELLIGENCE</small></div>',unsafe_allow_html=True)
        st.caption('Graph insight. Temporal context.')
        page=st.radio('Workspace',PAGES,key='navigation')
        st.divider()
        st.markdown('**Monitoring simulation**')
        st.caption('Historical Elliptic test-period replay. No live blockchain source is connected.')
        cols=st.columns(3)
        cols[0].button('Start',on_click=replay_action,args=('start',),key='start',width='stretch')
        cols[1].button('Pause',on_click=replay_action,args=('pause',),key='pause',width='stretch')
        cols[2].button('Reset',on_click=replay_action,args=('reset',),key='reset',width='stretch')
        st.slider('Monitoring Period',42,49,key='scrub_period',on_change=scrub,
                  help='Replay cursor. Only records through this period appear in monitoring and investigation views.')
        st.select_slider('Seconds per period',[1,2,3,5,10],value=3,key='replay_speed',on_change=speed_changed)
        state=st.session_state.replay
        status='ACTIVE' if state['running'] else 'COMPLETE' if state['period']==49 else 'PAUSED'
        st.caption(f"Replay: {status} · Updated: {state['updated']}")
        st.progress((state['period']-41)/8)
        with st.expander('Threshold exploration'):
            st.checkbox('Enable exploratory rules',key='explore')
            st.slider('Population score threshold',0.0,100.0,step=.1,key='explore_level',disabled=not st.session_state.explore)
            st.slider('Increase threshold (points)',0.0,100.0,step=.1,key='explore_increase',disabled=not st.session_state.explore)
            st.caption('Only changes the exploratory warning view. The original model threshold, benchmark and alert feed stay frozen.')
        with st.expander('Technical information'):
            st.write(f'Frozen transaction threshold: {a.threshold*100:.1f} / 100.')
            st.write(f'Display bands: Low below {a.threshold*LOW_FRACTION_OF_DECISION*100:.0f}; '
                     f'Watch below {a.threshold*100:.0f}; High below {CRITICAL_SCORE*100:.0f}; Critical at or above {CRITICAL_SCORE*100:.0f}.')
            st.caption('Bands are presentation-only cutoffs, configured in intelligence/config.py. Scores are uncalibrated.')
            st.write('Training 1–34 · Validation 35–41 · Test 42–49. Inference: CPU.')
        st.caption('Anonymous transaction references. Academic research prototype.')

    @st.fragment(run_every=1 if st.session_state.replay['running'] else None)
    def replay_clock():
        previous=st.session_state.replay
        updated=advance(previous,time.monotonic(),st.session_state.replay_speed)
        if updated['period']!=previous['period']:
            st.session_state.replay=updated
            st.rerun()
    replay_clock()
    frozen_feed=a.period_table(a.risk_periods(st.session_state.replay['period']))
    st.session_state.alert_list=frozen_feed[frozen_feed['Frozen Escalation Flag']].to_dict('records')
    handlers=dict(zip(PAGES,[views.command_center,views.transaction_intelligence,views.temporal_risk,
                            views.early_warnings,views.network_investigation,views.model_intelligence]))
    try:
        handlers[page](a,st.session_state.replay['period'],lambda:load_engine(str(ARTIFACT_DIR)))
    except Exception as exc:
        st.error('This view could not be rendered. Your saved model and results have not been changed.')
        with st.expander('Technical error details'):st.code(str(exc))


if __name__=='__main__':
    main()
