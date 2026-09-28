"""Regenerate this case from the frozen candidate."""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__),
                                '..', '..', '..', 'tests',
                                'leclaire_cg'))
import pass06
pass06.run_one(2, out_root=os.path.join(os.path.dirname(__file__), '..'))
