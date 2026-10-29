"""Verify only public CSV evidence: no models, raw inputs, DGP or file writes.

NumPy is used only for the frozen whole-mechanism Bootstrap. All other checks
use the Python standard library. Hashes authenticate public bytes, not private
source authenticity. This program never runs an experiment or original validator.
"""
import argparse
from collections import defaultdict
import csv
import hashlib
import itertools
import json
import math
from pathlib import Path
import re
import statistics
import unittest

METHODS = ('j', 'kernel-old', 'kernel-new')
ARMS = ('00', '01', '10', '11')
EFFECTS = ('direct', 'spillover', 'total')
MIDS = tuple(range(1000, 1020))
RIDS = tuple(range(10))
REASONS = ('conditional_structural_zero', 'assignment_zero', 'observation_sampling_zero', 'covered')
ERRORS = ('true_mean', 'pred_mean', 'bias', 'mae', 'mse', 'rmse')
EXTRAS = ('center_minus_leaf_bias', 'center_minus_leaf_mae', 'center_minus_leaf_rmse')
COUNTS = {'context_identity.csv':400, 'ate_context_metrics.csv':3600,
          'response_context.csv':9600, 'effects_context.csv':7200,
          'effect_center_leaf_context.csv':3600, 'support_context.csv':9600,
          'frozen_metrics_context.csv':2400, 'support_paired_arm_contrasts.csv':2400}
META = 'context_id mechanism_id pair_repeat_id center_t method center_observed category'.split()
ATE_OLD = 'family mechanism repeat m_observed context_id method estimand effect interval_level point_requested point_valid error_sum squared_error_sum interval_requested interval_valid covered width_sum prediction_failure interval_status bias rmse coverage coverage_including_failures mean_width interval_success_rate'.split()
SCHEMAS = {
 'context_identity.csv':'context_id mechanism_id pair_repeat_id center_t'.split(),
 'ate_context_metrics.csv':ATE_OLD+'mechanism_id pair_repeat_id center_t interval_failure ate_true ate_pred ate_lower ate_upper'.split(),
 'response_context.csv':META+'n_nodes arm'.split()+list(ERRORS),
 'effects_context.csv':META+'n_nodes effect model_effect_supported'.split()+list(ERRORS),
 'effect_center_leaf_context.csv':META+'n_nodes effect'.split()+list(ERRORS)+list(EXTRAS),
 'support_context.csv':META+'arm full_graph_count observed_count empirical_support support_reason arm_rmse structurally_allowed assignment_produced observed_covered model_arm_supported'.split(),
 'frozen_metrics_context.csv':META+['arm_rmse']+[e+'_'+s for e in EFFECTS for s in ('rmse','bias','ate_true','ate_pred')],
 'support_paired_arm_contrasts.csv':'method mechanism_id pair_repeat_id arm structural_rmse allowed_rmse allowed_empirical_support delta'.split(),
}
STRINGS = set('context_id method category arm effect estimand interval_status support_reason bootstrap_unit interpretation metric scope'.split())
BOOLS = set('center_observed model_effect_supported empirical_support structurally_allowed assignment_produced observed_covered model_arm_supported prediction_failure interval_failure ranked partial_support allowed_empirical_support'.split())
INTS = set('family mechanism mechanism_id repeat pair_repeat_id center_t m_observed n_nodes contexts mechanisms repeats_per_mechanism repeats independent_units bootstrap_seed bootstrap_draws point_requested point_valid interval_requested interval_valid covered prediction_failure_contexts contexts_used contexts_expected mechanisms_used mechanisms_expected interval_failed truth_below_lower truth_above_upper opposite_sign_point requested valid context_state_cases count'.split())


def need(value, label):
    if not value:
        raise ValueError(label)


def near(actual, expected, label='numeric disagreement', tolerance=1e-11):
    a, b = float(actual), float(expected)
    need((math.isnan(a) and math.isnan(b)) or math.isclose(a,b,rel_tol=tolerance,abs_tol=tolerance), label)


def mean(values):
    return statistics.fmean(values)


def number(value):
    return math.nan if value == 'N/A' else float(value)


def parse(row):
    result = {}
    for k,v in row.items():
        if k in STRINGS or v == '' or (k == 'center_t' and v == 'all'):
            result[k] = v
        elif k in BOOLS:
            need(v in ('True','False'), 'invalid boolean '+k)
            result[k] = v == 'True'
        elif k in INTS or (k.endswith('_count') and not k.startswith('mean_')):
            need(re.fullmatch(r'-?\d+',v) is not None, 'invalid integer '+k)
            result[k] = int(v)
        else:
            result[k] = number(v)
    return result


def check_digest(raw, expected, label='file'):
    need(hashlib.sha256(raw).hexdigest()==expected, 'SHA256 mismatch '+label)


def load_csv(path):
    with path.open(encoding='utf-8',newline='') as f:
        reader=csv.DictReader(f);rows=list(reader);columns=reader.fieldnames
        need(columns is not None and len(columns)==len(set(columns)), 'missing/duplicate CSV columns')
    return columns,rows


def groups(rows, keys):
    out=defaultdict(list)
    for r in rows:out[tuple(r[k] for k in keys)].append(r)
    return out


def grid(rows, keys, expected, label):
    keys_found=[tuple(r[k] for k in keys) for r in rows]
    need(len(keys_found)==len(set(keys_found)) and set(keys_found)==set(expected), 'missing/duplicate/unexpected '+label)


def compare(actual, expected, keys, label):
    indexed={tuple(str(r[k]) for k in keys):r for r in actual}
    need(len(indexed)==len(actual)==len(expected),label+' row count/duplicates')
    for wanted in expected:
        key=tuple(str(wanted[k]) for k in keys)
        need(key in indexed,label+' missing row')
        row=indexed[key];need(set(row)==set(wanted),label+' schema')
        for k,v in wanted.items():
            if isinstance(v,float):near(row[k],v,label+' '+k)
            else:need(row[k]==v,label+' '+k)
    return len(actual)


def check_metadata(rows, identities):
    for row in rows:
        need(row['context_id'] in identities,'unknown context')
        for k in ('mechanism_id','pair_repeat_id','center_t'):
            need(row[k]==identities[row['context_id']][k], 'identity projection mismatch '+k)
        if 'method' in row:need(row['method'] in METHODS,'unknown method')
        if 'repeat' in row:need(row['repeat']==row['pair_repeat_id'],'repeat is not pair repeat')
        if 'mechanism' in row:need(row['mechanism']==row['mechanism_id'],'mechanism alias mismatch')


def check_ate(row):
    need(row['estimand']=='ATE' and row['m_observed']==50 and row['interval_level']==.95,'ATE definition')
    need(math.isfinite(row['ate_true']),'nonfinite ATE truth')
    valid=math.isfinite(row['ate_pred']) and not row['prediction_failure']
    j=row['method']=='j'
    interval_valid=j and not row['interval_failure'] and math.isfinite(row['ate_lower']) and math.isfinite(row['ate_upper']) and row['ate_lower']<=row['ate_upper']
    error=row['ate_pred']-row['ate_true'] if valid else 0.
    hit=int(interval_valid and row['ate_lower']<=row['ate_true']<=row['ate_upper'])
    width=row['ate_upper']-row['ate_lower'] if interval_valid else 0.
    expected=dict(point_requested=1,point_valid=int(valid),error_sum=error,squared_error_sum=error**2,
        interval_requested=int(j),interval_valid=int(interval_valid),covered=hit,width_sum=width,
        bias=error if valid else math.nan,rmse=abs(error) if valid else math.nan,
        coverage=float(hit) if interval_valid else math.nan,
        coverage_including_failures=float(hit) if j else math.nan,
        mean_width=width if interval_valid else math.nan,interval_success_rate=float(interval_valid) if j else math.nan)
    for k,v in expected.items():near(row[k],v,'ATE metric '+k)
    need(row['interval_status']==('unsupported' if not j else 'ok' if interval_valid else 'failed_or_invalid'),'interval status')
    if not j:
        need(not row['interval_failure'] and math.isnan(row['ate_lower']) and math.isnan(row['ate_upper']),'baseline unsupported semantics')


def support_reason(row):
    full,observed=row['full_graph_count'],row['observed_count']
    limit=1 if row['category']=='center' else 199
    need(0<=observed<=full<=limit,'invalid Support counts')
    impossible=int(row['arm'][1])!=row['center_t'] if row['category']=='leaf' else int(row['arm'][0])!=row['center_t']
    if impossible:
        need(full==observed==0,'impossible state has observations')
        return REASONS[0]
    return REASONS[1] if full==0 else REASONS[2] if observed==0 else REASONS[3]


def error_summary(rows, target, level, extra=()):
    keys=['method','center_t','category',target]
    if level=='mechanism':keys.insert(1,'mechanism_id')
    result=[]
    for key,members in groups(rows,keys).items():
        need(len(members)==(10 if level=='mechanism' else 20),'error aggregation group incomplete')
        stats={f:mean(r[f] for r in members) for f in (*ERRORS,*extra)}
        result.append(dict(zip(keys,key),n_nodes=members[0]['n_nodes'],contexts=10 if level=='mechanism' else 200,
            mechanisms=1 if level=='mechanism' else 20,repeats_per_mechanism=10,**stats,
            mean_context_rmse=stats['rmse'],pooled_rmse=math.sqrt(stats['mse'])))
    return result,keys


def support_summary(rows, level):
    keys=['method','center_t','category','arm']
    if level=='mechanism':keys.insert(1,'mechanism_id')
    flags=('structurally_allowed','assignment_produced','observed_covered','model_supported')
    result=[]
    for key,members in groups(rows,keys).items():
        need(len(members)==(10 if level=='mechanism' else 20),'Support aggregation group incomplete')
        contexts=10 if level=='mechanism' else 200
        if level=='mechanism':
            counts={s+'_count':sum(r['support_reason']==s for r in members) for s in REASONS}
            counts.update({f+'_count':sum(r['model_arm_supported'] if f=='model_supported' else r[f] for r in members) for f in flags})
            rates={k[:-6]+'_rate':v/contexts for k,v in counts.items()}
            rates.update({'mean_'+k:mean(r[k] for r in members) for k in ('full_graph_count','observed_count','arm_rmse')})
            rates['center_observed_rate']=mean(r['center_observed'] for r in members)
        else:
            count_fields=[s+'_count' for s in REASONS]+[f+'_count' for f in flags]
            counts={k:sum(r[k] for r in members) for k in count_fields}
            rates={k:mean(r[k] for r in members) for k in members[0] if k.startswith('mean_') or k.endswith('_rate')}
        result.append(dict(zip(keys,key),contexts=contexts,mechanisms=1 if level=='mechanism' else 20,**counts,**rates))
    return result,keys


def ate_group(members):
    per_mechanism=groups(members,('family','mechanism'))
    complete=[v for v in per_mechanism.values() if all(r['point_requested']==r['point_valid']==1 for r in v)]
    requested=sum(r['interval_requested'] for r in members);valid=sum(r['interval_valid'] for r in members);hits=sum(r['covered'] for r in members)
    return dict(absolute_conditional_bias=mean(abs(mean(r['error_sum'] for r in v)) for v in complete) if complete else math.nan,
        variance_unbiased=mean(statistics.variance(r['error_sum'] for r in v) for v in complete) if complete and all(len(v)>1 for v in complete) else math.nan,
        rmse=math.sqrt(mean(mean(r['squared_error_sum'] for r in v) for v in complete)) if complete else math.nan,
        mechanisms_used=len(complete),mechanisms_expected=len(per_mechanism),contexts_used=sum(map(len,complete)),contexts_expected=len(members),
        ranked=len(complete)>0 and len(complete)==len(per_mechanism),interval_level=.95,interval_requested=requested,interval_valid=valid,covered=hits,
        coverage=hits/valid if valid else math.nan,coverage_including_failures=hits/requested if requested else math.nan)


def bootstrap(values):
    import numpy as np  # No model package; retain the frozen PCG64 stream exactly.
    values=np.asarray(values,dtype=float);rng=np.random.default_rng(2026102502)
    draws=values[rng.integers(0,len(values),size=(10000,len(values)))].mean(axis=1)
    return float(values.mean()),*map(float,np.quantile(draws,[.025,.975]))


def verify_tables(data, references):
    identity=data['context_identity.csv'];identities={r['context_id']:r for r in identity}
    expected={(f'f0_m{m}_r{2*r+c}_observed50',m,r,c) for m in MIDS for r in RIDS for c in (0,1)}
    grid(identity,('context_id','mechanism_id','pair_repeat_id','center_t'),expected,'identity grid')
    contexts=set(identities);method_contexts=set(itertools.product(contexts,METHODS))
    for name,rows in data.items():
        need(len(rows)==COUNTS[name],name+' count')
        if name!='support_paired_arm_contrasts.csv':check_metadata(rows,identities)
    for name,target,values,cats in [('ate_context_metrics.csv','effect',EFFECTS,None),('response_context.csv','arm',ARMS,('center','leaf')),
        ('effects_context.csv','effect',EFFECTS,('center','leaf')),('effect_center_leaf_context.csv','effect',EFFECTS,('center_minus_leaf',)),
        ('support_context.csv','arm',ARMS,('center','leaf'))]:
        keys=('context_id','method',target) if cats is None else ('context_id','method','category',target)
        expected_keys={(c,m,v) for c,m in method_contexts for v in values} if cats is None else {(c,m,cat,v) for c,m in method_contexts for cat in cats for v in values}
        grid(data[name],keys,expected_keys,name)
    grid(data['frozen_metrics_context.csv'],('context_id','method','category'),{(c,m,cat) for c,m in method_contexts for cat in ('center','leaf')},'frozen metrics')
    ate=data['ate_context_metrics.csv'];response=data['response_context.csv'];effects=data['effects_context.csv'];difference=data['effect_center_leaf_context.csv'];support=data['support_context.csv'];native=data['frozen_metrics_context.csv']
    for row in ate:check_ate(row)
    for row in response+effects+difference:
        need(all(math.isfinite(row[k]) for k in ERRORS),'nonfinite node metric')
        near(row['bias'],row['pred_mean']-row['true_mean'],'node bias')
        near(row['rmse']**2,row['mse'],'context RMSE/MSE')
        need(row['mse']>=0 and row['mae']+1e-11>=abs(row['bias']) and row['rmse']+1e-11>=row['mae'],'error inequalities')
        need(row['n_nodes']==(199 if row['category']=='leaf' else 1),'node category size')
    ri={(r['context_id'],r['method'],r['category'],r['arm']):r for r in response}
    ei={(r['context_id'],r['method'],r['category'],r['effect']):r for r in effects}
    ni={(r['context_id'],r['method'],r['category']):r for r in native}
    ai={(r['context_id'],r['method'],r['effect']):r for r in ate}
    si={(r['context_id'],r['method'],r['category'],r['arm']):r for r in support}
    for r in effects:
        arms={'direct':('10','00'),'spillover':('11','10'),'total':('11','00')}[r['effect']]
        for field in ('true_mean','pred_mean','bias'):
            near(r[field],ri[r['context_id'],r['method'],r['category'],arms[0]][field]-ri[r['context_id'],r['method'],r['category'],arms[1]][field],'state/effect definition')
        old=ni[r['context_id'],r['method'],r['category']]
        for field,suffix in [('true_mean','ate_true'),('pred_mean','ate_pred'),('bias','bias'),('rmse','rmse')]:near(r[field],old[r['effect']+'_'+suffix],'frozen effect mapping')
    for c,m in method_contexts:
        for cat in ('center','leaf'):
            near(ni[c,m,cat]['arm_rmse'],math.sqrt(mean(ri[c,m,cat,a]['mse'] for a in ARMS)),'four-state combined response')
        for effect in EFFECTS:
            for field,ate_field in [('true_mean','ate_true'),('pred_mean','ate_pred')]:
                near((ei[c,m,'center',effect][field]+199*ei[c,m,'leaf',effect][field])/200,ai[c,m,effect][ate_field],'node/population ATE link',2e-6)
    for r in difference:
        center=ei[r['context_id'],r['method'],'center',r['effect']];leaf=ei[r['context_id'],r['method'],'leaf',r['effect']]
        for field in ('true_mean','pred_mean','bias'):near(r[field],center[field]-leaf[field],'center-leaf contrast')
        for field in ('bias','mae','rmse'):near(r['center_minus_leaf_'+field],center[field]-leaf[field],'difference of error metrics')
        near(r['mae'],abs(r['bias']));near(r['mse'],r['bias']**2)
    for r in support:
        reason=support_reason(r);need(r['support_reason']==reason,'Support reason mismatch')
        for field,value in [('empirical_support',r['observed_count']>0),('structurally_allowed',reason!=REASONS[0]),('assignment_produced',r['full_graph_count']>0),('observed_covered',r['observed_count']>0)]:need(r[field]==value,'Support stage '+field)
        near(r['arm_rmse'],ri[r['context_id'],r['method'],r['category'],r['arm']]['rmse'])
    for c,m in method_contexts:
        obs=ni[c,m,'center']['center_observed']
        for cat,n in [('center',1),('leaf',199)]:
            rr=[si[c,m,cat,a] for a in ARMS];need(sum(r['full_graph_count'] for r in rr)==n,'Support full counts')
            need(sum(r['observed_count'] for r in rr)==(int(obs) if cat=='center' else 50-int(obs)),'Support observed counts')
            need(all(r['center_observed']==obs for r in rr),'center observation identity')
        for cat in ('center','leaf'):
            for arm in ARMS:
                r=si[c,m,cat,arm];base=si[c,'j',cat,arm]
                for k in ('full_graph_count','observed_count','support_reason','center_observed'):need(r[k]==base[k],'methods have different empirical Support')
    checked=0
    def check(name,expected,keys):
        nonlocal checked
        checked+=compare(references['../node_support/'+name+'.csv'],expected,keys,name)
    for stem,rows,target,extra in [('response',response,'arm',()),('effects',effects,'effect',()),('effect_center_leaf',difference,'effect',EXTRAS)]:
        mechanism,keys=error_summary(rows,target,'mechanism',extra);check(stem+'_mechanism',mechanism,keys)
        overall,keys=error_summary(mechanism,target,'overall',extra);check(stem+'_overall_by_center',overall,keys)
    mechanism,keys=support_summary(support,'mechanism');check('support_mechanism',mechanism,keys)
    overall,keys=support_summary(mechanism,'overall');check('support_overall_by_center',overall,keys)
    secondary=[];keys=('method','mechanism_id','center_t','category')
    for key,rr in groups(native,keys).items():
        need(len(rr)==10,'frozen metric repeat completeness')
        secondary.append(dict(zip(keys,key),**{k:mean(r[k] for r in rr) for k in rr[0] if k not in (*keys,'context_id','pair_repeat_id','center_observed')}))
    check('frozen_metrics_mechanism',secondary,keys)
    counts=[]
    for key,rr in groups(support,('method','center_t','category')).items():
        for reason in REASONS:
            count=sum(r['support_reason']==reason for r in rr)
            counts.append(dict(zip(('method','center_t','category'),key),support_reason=reason,context_state_cases=800,count=count,mechanism_equal_rate=count/800,mechanisms=20))
    check('support_reason_counts_by_center',counts,('method','center_t','category','support_reason'))
    paired=data['support_paired_arm_contrasts.csv'];grid(paired,('method','mechanism_id','pair_repeat_id','arm'),itertools.product(METHODS,MIDS,RIDS,ARMS),'paired contrasts')
    for r in paired:
        c=int(r['arm'][1]);mid=r['mechanism_id'];rid=r['pair_repeat_id'];m=r['method']
        allowed=si[f'f0_m{mid}_r{2*rid+c}_observed50',m,'leaf',r['arm']];blocked=si[f'f0_m{mid}_r{2*rid+1-c}_observed50',m,'leaf',r['arm']]
        near(r['allowed_rmse'],allowed['arm_rmse']);near(r['structural_rmse'],blocked['arm_rmse']);near(r['delta'],blocked['arm_rmse']-allowed['arm_rmse'])
        need(r['allowed_empirical_support']==allowed['empirical_support'],'paired empirical Support')
    primary=[];summaries=[]
    for m in METHODS:
        values=[]
        for mid in MIDS:
            repeats=[mean(r['delta'] for r in paired if r['method']==m and r['mechanism_id']==mid and r['pair_repeat_id']==rid) for rid in RIDS]
            value=mean(repeats);values.append(value);primary.append(dict(method=m,mechanism_id=mid,repeats=10,primary_delta=value))
        value,lo,hi=bootstrap(values)
        summaries.append(dict(method=m,mean_delta=value,ci95_lower=lo,ci95_upper=hi,independent_units=20,bootstrap_seed=2026102502,bootstrap_draws=10000,bootstrap_unit='whole mechanism',interpretation='Conditional association; not a causal effect of Support'))
    check('support_primary_by_mechanism',primary,('method','mechanism_id'));check('support_primary_summary',summaries,('method',))
    coverage={}
    for label,center in [('overall',None),('center_t0',0),('center_t1',1)]:
        rows=[r for r in ate if center is None or r['center_t']==center];table=[];figure=[]
        for m in METHODS:
            for effect in EFFECTS:
                members=[r for r in rows if r['method']==m and r['effect']==effect]
                table.append(dict(method=m,m_observed=50,effect=effect,**ate_group(members)))
                for scope,mid in [('pooled',None)]+[('mechanism',mid) for mid in MIDS]:
                    rr=members if mid is None else [r for r in members if r['mechanism_id']==mid];valid=sum(r['point_valid'] for r in rr);requested=sum(r['point_requested'] for r in rr)
                    figure.append(dict(method=m,estimand='ATE',effect=effect,metric='rmse',scope=scope,family='' if mid is None else 0,mechanism='' if mid is None else mid,
                        estimate=math.sqrt(sum(r['squared_error_sum'] for r in rr)/valid) if valid else math.nan,requested=requested,valid=valid,contexts=len(rr),prediction_failure_contexts=sum(r['prediction_failure'] for r in rr),partial_support=valid<requested))
        checked+=compare(references[f'../preview/{label}/ate_m50.csv'],table,('method','effect'),label+' point table')
        checked+=compare(references[f'../preview/{label}/ate_accuracy_source.csv'],figure,('method','effect','scope','mechanism'),label+' figure source')
        coverage[label]=[{k:r[k] for k in ('effect','covered','interval_requested','interval_valid','coverage_including_failures')} for r in table if r['method']=='j']
    diagnostic=[]
    for mid in MIDS:
        for effect in EFFECTS:
            for center in ('all',0,1):
                rr=[r for r in ate if r['method']=='j' and r['mechanism_id']==mid and r['effect']==effect and (center=='all' or r['center_t']==center)]
                requested=sum(r['interval_requested'] for r in rr);valid=sum(r['interval_valid'] for r in rr)
                diagnostic.append(dict(mechanism=mid,center_t=center,effect=effect,covered=sum(r['covered'] for r in rr),interval_requested=requested,interval_valid=valid,interval_failed=requested-valid,
                    mean_width=sum(r['width_sum'] for r in rr)/valid if valid else math.nan,mean_error=mean(r['error_sum'] for r in rr),
                    truth_below_lower=sum(math.isfinite(r['ate_lower']) and r['ate_true']<r['ate_lower'] for r in rr),truth_above_upper=sum(math.isfinite(r['ate_upper']) and r['ate_true']>r['ate_upper'] for r in rr),opposite_sign_point=sum(math.isfinite(r['ate_pred']) and r['ate_true']*r['ate_pred']<0 for r in rr)))
    checked+=compare(references['../preview/j_coverage_by_mechanism_and_center.csv'],diagnostic,('mechanism','center_t','effect'),'mechanism-center diagnostics')
    return dict(passed=True,contexts=400,methods=3,mechanisms=20,pairs=200,csv_rows={k:len(v) for k,v in data.items()},reference_rows_recomputed=checked,coverage=coverage,
        publicly_recomputed=['ATE scalar errors/interval membership/coverage/denominators','node effect mean definitions and center-leaf contrasts','context-to-mechanism-to-overall summaries','Support reasons from published counts','paired Support contrasts and mechanism Bootstrap','published ATE tables, figure source and center diagnostics'],
        not_independently_verifiable=['Identity authenticity against private receipts (only a minimal public projection is provided)','Leaf MAE/MSE from individual node errors: individual arrays are not public','Support counts from original assignments and observation indices: factual inputs are not public','Model inference, posterior mathematics for all contexts, or complete frozen-source acceptance'])


def verify(directory):
    directory=Path(directory).resolve();manifest=json.loads((directory/'PUBLIC_EVIDENCE_MANIFEST.json').read_text(encoding='utf-8'))
    need(manifest['protocol']=='e1_5_public_context_evidence_v1','manifest protocol')
    need(manifest['design']==dict(mechanism_ids=list(MIDS),pair_repeat_ids=list(RIDS),center_states=[0,1],contexts=400,methods=list(METHODS),n_nodes=200,n_observed=50,effect_order=list(EFFECTS),interval_level=.95),'manifest design')
    expected=set(COUNTS)|{'.gitattributes','README.md','verify_public_evidence.py'}
    records=manifest['files'];need({r['path'] for r in records}==expected and len(records)==len(expected),'manifest public inventory')
    need({p.name for p in directory.iterdir()}==expected|{'PUBLIC_EVIDENCE_MANIFEST.json'},'unexpected public files')
    data={};references={}
    for record in records+manifest['reference_files']:
        path=(directory/record['path']).resolve()
        need(path.is_relative_to(directory.parent),'path outside public submission')
        raw=path.read_bytes();check_digest(raw,record['sha256'],record['path'])
        need(len(raw)==record['bytes'],'byte count '+record['path'])
        if path.suffix=='.csv':
            columns,rows=load_csv(path);need(columns==record['columns'] and len(rows)==record['rows'],'CSV schema/count '+record['path'])
            if record['path'] in COUNTS:
                need(set(columns)==set(SCHEMAS[record['path']]),'required columns '+record['path'])
                for row in rows:
                    if record['path']=='ate_context_metrics.csv' and row['method']!='j':
                        need(all(row[k]=='N/A' for k in ('ate_lower','ate_upper','coverage','coverage_including_failures','mean_width','interval_success_rate')),'baseline N/A representation')
                data[record['path']]=list(map(parse,rows))
            else:references[record['path']]=list(map(parse,rows))
    expected_refs={'../node_support/'+name+'.csv' for name in ('response_mechanism','response_overall_by_center','effects_mechanism','effects_overall_by_center','effect_center_leaf_mechanism','effect_center_leaf_overall_by_center','support_mechanism','support_overall_by_center','frozen_metrics_mechanism','support_primary_by_mechanism','support_primary_summary','support_reason_counts_by_center')}
    expected_refs|={f'../preview/{label}/{name}.csv' for label in ('overall','center_t0','center_t1') for name in ('ate_m50','ate_accuracy_source')}
    expected_refs.add('../preview/j_coverage_by_mechanism_and_center.csv')
    need(set(references)==expected_refs and len(manifest['reference_files'])==19,'reference inventory')
    result=verify_tables(data,references);result.update(public_files_hashed=len(records),reference_files_hashed=19,manifest_self_hash='Not self-authenticated; compare the externally reported digest or Git revision',writes=0)
    return result


class DeterministicChecks(unittest.TestCase):
    def test_duplicate_and_missing_grid(self):
        with self.assertRaises(ValueError):grid([{'id':1},{'id':1}],('id',),[(1,),(2,)],'fixture')
        with self.assertRaises(ValueError):grid([{'id':1}],('id',),[(1,),(2,)],'fixture')
    def test_pair_center_identity(self):
        ids={'x':dict(mechanism_id=1000,pair_repeat_id=2,center_t=1)}
        check_metadata([dict(context_id='x',mechanism_id=1000,pair_repeat_id=2,center_t=1,repeat=2)],ids)
        with self.assertRaises(ValueError):check_metadata([dict(context_id='x',mechanism_id=1000,pair_repeat_id=2,center_t=0)],ids)
    def test_encoded_repeat_rejected(self):
        ids={'x':dict(mechanism_id=1000,pair_repeat_id=2,center_t=1)}
        with self.assertRaises(ValueError):check_metadata([dict(context_id='x',mechanism_id=1000,pair_repeat_id=2,center_t=1,repeat=5)],ids)
    def test_failure_denominator_retained(self):
        rows=[dict(family=0,mechanism=1,point_requested=1,point_valid=1,error_sum=0.,squared_error_sum=0.,interval_requested=1,interval_valid=v,covered=v) for v in (1,0)]
        r=ate_group(rows);self.assertEqual(r['coverage'],1.);self.assertEqual(r['coverage_including_failures'],.5)
    def test_baseline_interval_na(self):
        rows=[dict(family=0,mechanism=1,point_requested=1,point_valid=1,error_sum=0.,squared_error_sum=0.,interval_requested=0,interval_valid=0,covered=0)]
        self.assertTrue(math.isnan(ate_group(rows)['coverage_including_failures']))
    def test_mechanism_equal_stats(self):
        rows=[dict(family=0,mechanism=m,point_requested=1,point_valid=1,error_sum=e,squared_error_sum=e*e,interval_requested=0,interval_valid=0,covered=0) for m,errors in [(1,(1.,3.)),(2,(-2.,0.))] for e in errors]
        r=ate_group(rows);near(r['rmse'],math.sqrt(3.5));near(r['absolute_conditional_bias'],1.5);near(r['variance_unbiased'],2.)
    def test_macro_rmse_differs_from_pooled(self):
        rows=[dict(method='j',mechanism_id=1000,center_t=0,category='center',arm='00',n_nodes=1,true_mean=0.,pred_mean=e,bias=e,mae=e,mse=e*e,rmse=e) for e in (1.,3.)*5]
        result,_=error_summary(rows,'arm','mechanism');near(result[0]['rmse'],2.);near(result[0]['pooled_rmse'],math.sqrt(5.))
    def test_four_support_reasons_and_invalid_counts(self):
        base=dict(category='leaf',center_t=0,arm='01',full_graph_count=0,observed_count=0)
        self.assertEqual(support_reason(base),REASONS[0]);self.assertEqual(support_reason(dict(base,arm='00')),REASONS[1])
        self.assertEqual(support_reason(dict(base,arm='00',full_graph_count=2)),REASONS[2])
        self.assertEqual(support_reason(dict(base,arm='00',full_graph_count=2,observed_count=1)),REASONS[3])
        with self.assertRaises(ValueError):support_reason(dict(base,observed_count=1))
    def test_constant_mechanism_bootstrap(self):
        self.assertEqual(bootstrap([5.,5.]),(5.,5.,5.))
    def test_hash_tampering_and_na_comparison(self):
        check_digest(b'a',hashlib.sha256(b'a').hexdigest())
        with self.assertRaises(ValueError):check_digest(b'b',hashlib.sha256(b'a').hexdigest())
        near(number('N/A'),math.nan)
        with self.assertRaises(ValueError):near(0.,math.nan)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--directory',type=Path,default=Path(__file__).resolve().parent)
    parser.add_argument('--self-test',action='store_true')
    args=parser.parse_args()
    if args.self_test:
        result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(DeterministicChecks))
        raise SystemExit(0 if result.wasSuccessful() else 1)
    print(json.dumps(verify(args.directory),indent=2,allow_nan=False))