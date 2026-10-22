"""Synthetic evidence-assembly demo. No LLM, embeddings or real connectors.
Checks mechanical provenance/version/visibility contracts, not semantic entailment.
"""
import copy
import hashlib
import json
import platform
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def fixture():
    def chunk(cid, source, version, text, kind, **kw):
        return dict(id=cid, source=source, version=version, text=text, kind=kind,
                    groups=['analyst'], valid_from='2026-10-01', valid_to=None, **kw)
    chunks = [
        chunk('definition', 'confluence:demo:page-10', 3,
              'demo.sales.orders.net_amount：净成交金额，排除退款。状态码见退款章节。', 'policy'),
        chunk('refund', 'confluence:demo:page-10', 3,
              '退款章节：status=REFUNDED 的订单不计入净成交金额。', 'policy'),
        chunk('sql', 'dap:demo:job-7', 2,
              'SELECT SUM(amount) FROM demo.sales.orders WHERE is_test = false;', 'implementation'),
        chunk('lineage', 'lineage:demo:edge-8', 1,
              'job-7 generates demo.sales.orders.net_amount; job-7 consumes topic-orders.', 'runtime_metadata'),
        chunk('topic', 'mq:demo:topic-orders', 4,
              'topic-orders 的生产者为 demo.order-service；这里只保存元数据。', 'queue_metadata'),
        chunk('decision', 'dingtalk:demo:message-6', 1,
              '讨论稿：建议下月调整退款口径，尚未批准。', 'discussion', decision_state='draft'),
        chunk('collision', 'confluence:demo:page-99', 1,
              'demo.finance.orders.net_amount：会计口径；同名不表示同一字段。', 'policy'),
    ]
    def edge(a,b,rel,ev,quote):
        return dict(source=a,target=b,relation=rel,evidence=ev,quote=quote,verified=True)
    edges = [
        edge('definition','refund','requires_context','definition','状态码见退款章节'),
        edge('definition','sql','implemented_by','lineage','job-7 generates demo.sales.orders.net_amount'),
        edge('sql','topic','consumes','lineage','job-7 consumes topic-orders'),
        edge('definition','decision','discussed_in','decision','建议下月调整退款口径'),
    ]
    return {'synthetic':True,'chunks':chunks,'edges':edges,
            'heads':{c['source']:c['version'] for c in chunks}}


def assemble(data, seed, groups=('analyst',), as_of='2026-10-21', max_chunks=8, max_depth=3):
    nodes={c['id']:c for c in data['chunks']}
    allowed={'requires_context','implemented_by','consumes','discussed_in'}
    def readable(c):
        return (bool(set(groups)&set(c['groups'])) and
                c['version']==data['heads'].get(c['source']) and
                c['valid_from']<=as_of and (c['valid_to'] is None or as_of<c['valid_to']))
    result={'synthetic':True,'mode':'mechanical_evidence_assembly',
            'seed':seed,'evidence':[],'paths':[],'gaps':[],
            'limitations':['No semantic entailment verification','No real connector or model',
                           'Current-version selection only; not historical reconstruction']}
    if seed not in nodes or not readable(nodes[seed]):
        result['gaps'].append('seed_unavailable');return result
    if max_chunks<1:
        result['gaps'].append('budget_exhausted');return result
    selected={seed};queue=[(seed,0)];expanded=set()
    while queue:
        current,depth=queue.pop(0)
        if current in expanded: continue
        expanded.add(current)
        for e in data['edges']:
            if e['source']!=current:continue
            if e['relation'] not in allowed or not e['verified']: continue
            target=nodes.get(e['target']);proof=nodes.get(e['evidence'])
            # Do not expose identifiers or content of inaccessible candidates in output.
            if not target or not proof or not readable(target) or not readable(proof):
                result['gaps'].append('branch_unavailable');continue
            if not e['quote'] or e['quote'] not in proof['text']:
                result['gaps'].append('invalid_provenance');continue
            if depth>=max_depth:
                result['gaps'].append('depth_limit');continue
            new={e['target'],e['evidence']}-selected
            if len(selected)+len(new)>max_chunks:
                result['gaps'].append('budget_exhausted');continue
            selected.update(new)
            result['paths'].append(copy.deepcopy(e))
            queue.append((e['target'],depth+1))
    result['evidence']=[copy.deepcopy(nodes[k]) for k in sorted(selected)]
    result['gaps']=sorted(set(result['gaps']))
    return result


def validate():
    checks=[]
    def check(name, predicate):
        if not predicate: raise AssertionError(name)
        checks.append({'case':name,'status':'pass'})
    def ids(out):return {x['id'] for x in out['evidence']}
    d=fixture();out=assemble(d,'definition')
    check('multi_system_chain', {'definition','refund','sql','lineage','topic','decision'}==ids(out))
    check('same_name_not_merged','collision' not in ids(out))
    x=copy.deepcopy(d)
    for c in x['chunks']:
        if c['id']=='lineage':c['groups']=['admin']
    out2=assemble(x,'definition')
    check('inaccessible_bridge_blocks_descendants',not {'sql','lineage','topic'}&ids(out2))
    check('no_inaccessible_source_in_payload','lineage:demo:edge-8' not in json.dumps(out2))
    x=copy.deepcopy(d);x['heads']['dap:demo:job-7']=3
    check('stale_version_blocks_branch',not {'sql','topic'}&ids(assemble(x,'definition')))
    x=copy.deepcopy(d)
    for c in x['chunks']:
        if c['id']=='refund':c['valid_to']='2026-10-21'
    check('validity_end_exclusive','refund' not in ids(assemble(x,'definition')))
    x=copy.deepcopy(d);x['edges'][1]['quote']='nonexistent fabricated link'
    check('fabricated_quote_blocks_edge','sql' not in ids(assemble(x,'definition')))
    small=assemble(d,'definition',max_chunks=2)
    check('budget_bound',len(small['evidence'])<=2 and 'budget_exhausted' in small['gaps'])
    x=copy.deepcopy(d);x['edges'].append(dict(source='refund',target='definition',relation='requires_context',evidence='definition',quote='状态码见退款章节',verified=True))
    check('cycle_terminates',len(assemble(x,'definition')['paths'])<=len(x['edges']))
    check('no_permission_no_evidence',assemble(d,'definition',groups=('guest',))['evidence']==[])
    check('discussion_stays_draft',next(c for c in out['evidence'] if c['id']=='decision')['decision_state']=='draft')
    return checks,out


if __name__=='__main__':
    start=datetime.now(timezone.utc).isoformat()
    checks,out=validate()
    (ROOT/'synthetic_fixture.json').write_text(json.dumps(fixture(),ensure_ascii=False,indent=2)+'\n')
    (ROOT/'demo_result.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n')
    record={'run_id':'synthetic-evidence-contract-20261021','kind':'deterministic_contract_checks',
            'command':'python3 prototype/evidence_chain.py','seed':'not applicable; deterministic',
            'dataset':'synthetic_fixture.json; hand-authored demo, not held-out benchmark',
            'source_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            'fixture_sha256':hashlib.sha256((ROOT/'synthetic_fixture.json').read_bytes()).hexdigest(),
            'python':sys.version,'platform':platform.platform(),'machine':platform.machine(),
            'started_at':start,'finished_at':datetime.now(timezone.utc).isoformat(),'exit_code':0,
            'checks':checks,'results':'prototype/demo_result.json',
            'claim_boundary':'No RAG quality, scalability, semantic verification or production ACL claims.'}
    (ROOT/'validation.json').write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({'passed':len(checks),'failed':0,'synthetic':True,'kind':record['kind']},ensure_ascii=False))
