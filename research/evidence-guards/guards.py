"""Policy-specific evidence gates over exact rendered development text.

No labels, construction records, split/view identifiers or model outputs enter
the gates. The grammar and three policies are a strong external program prior.
"""
import re
import sys
from pathlib import Path
GAP=Path(__file__).resolve().parent.parent/'evidence-gap'
sys.path.insert(0,str(GAP))
from gap_data import parse_text, keys, constraints

MAX_THRESHOLDS=(.5,.7,.9,.95,.99)
MARGIN_THRESHOLDS=(.2,.5,.8,.95)


def methods():
    return ['raw']+[f'maxprob_{t:g}' for t in MAX_THRESHOLDS]+[f'margin_{t:g}' for t in MARGIN_THRESHOLDS]+[
        'schema_presence','policy_determinacy','always_insufficient']


def parse_visible(state,policy):
    if 'Reviewer A rejection denies' in policy:
        raise ValueError('Composed policy is reserved and unsupported in this development follow-up')
    route=re.search(r'The target route names either (site-[A-Z]+) or (site-[A-Z]+)\.',policy)
    if route:family,sites='route_lookup',list(route.groups())
    elif 'Allow exactly when both reviewer A and reviewer B approve.' in policy:
        family,sites='joint_approval',['site-UNUSED_A','site-UNUSED_B']
    elif 'Use the target base decision, except reverse ALLOW and DENY' in policy:
        family,sites='reversal_exception',['site-UNUSED_A','site-UNUSED_B']
    else:raise ValueError('Unsupported policy grammar')
    return parse_text(state,policy,family,sites)


def gates(parsed):
    observations=constraints(parsed)
    conflict=[k for k,v in observations.items() if len(v)>1]
    missing=[k for k,v in observations.items() if not v]
    schema={'may_commit':not conflict and not missing,'missing_schema_fields':missing,'conflicting_schema_fields':conflict}
    if conflict:return schema,{'may_commit':False,'reason':'target_schema_conflict','certificate_fields':conflict}
    values={k:next(iter(v)) if v else None for k,v in observations.items()}
    family=parsed['family']
    if family=='joint_approval':
        rejecting=[k for k,v in values.items() if v is False]
        certificate=rejecting[:1] if rejecting else list(values) if not missing else []
        reason='explicit_rejection' if rejecting else 'both_approvals' if not missing else 'required_approval_missing'
    elif family=='reversal_exception':
        certificate=list(values) if not missing else []
        reason='base_and_exception_known' if certificate else 'base_or_exception_missing'
    elif family=='route_lookup':
        route=values['route']
        if route is not None:
            selected='site_b' if route else 'site_a'
            certificate=['route',selected] if values[selected] is not None else []
            reason='selected_permission_known' if certificate else 'selected_permission_missing'
        else:
            a,b=values['site_a'],values['site_b']
            certificate=['site_a','site_b'] if a is not None and a==b else []
            reason='every_possible_route_agrees' if certificate else 'route_undetermined'
    else:raise ValueError('Unsupported development policy')
    return schema,{'may_commit':bool(certificate),'reason':reason,'certificate_fields':certificate}


def decide(raw_prediction,probabilities,order,schema,policy,method):
    """Preserve the raw action, or map it to the semantic INSUFFICIENT label."""
    if method=='raw':keep=True;reason='unchanged'
    elif method=='always_insufficient':keep=False;reason='always_insufficient_control'
    elif method.startswith('maxprob_'):
        keep=max(probabilities)>=float(method.split('_')[1]);reason='fixed_max_probability_cutoff'
    elif method.startswith('margin_'):
        ordered=sorted(probabilities,reverse=True)
        keep=ordered[0]-ordered[1]>=float(method.split('_')[1]);reason='fixed_top_two_margin_cutoff'
    elif method=='schema_presence':keep=schema['may_commit'];reason='schema_presence_gate'
    elif method=='policy_determinacy':keep=policy['may_commit'];reason=policy['reason']
    else:raise ValueError('Unknown fixed method')
    prediction=raw_prediction if keep else 'INSUFFICIENT'
    return {'prediction':prediction,'gate_may_commit':keep,'reason':reason,
            'changed':prediction!=raw_prediction,'nominal_model_calls':0 if method=='always_insufficient' else 1,
            'uses_known_grammar':method in ('schema_presence','policy_determinacy')}
