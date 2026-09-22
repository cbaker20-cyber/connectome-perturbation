import json
import pytest
from scripts.pcdr_backend_input_check import check

def test_backend_schedule_mismatch_is_rejected(tmp_path):
    for seed in range(630801,630831):
      for c in ['baseline','lesion']:
       for b in ['numpy','cython']:
        p=tmp_path/b/f'{c}_{seed}';p.mkdir(parents=True)
        d={'status':'complete','seed':seed,'input_digest':'same','input_protocol':'fixed_binomial_tape_v1','duration_s':1,'dt_ms':.1,'input_hz':150,'context':'sugar','lesion_ids':[],'weight_scale':1,'inhibitory_scale':1,'strong_fraction':None}
        (p/'manifest.json').write_text(json.dumps(d))
    assert len(check(tmp_path))==60
    p=tmp_path/'cython/baseline_630801/manifest.json';d=json.loads(p.read_text());d['input_digest']='different';p.write_text(json.dumps(d))
    with pytest.raises(ValueError,match='input_digest'):check(tmp_path)
