"""Queenbee Results

The results are a combination of step inputs and outputs for a list of
runs.
"""

from typing import List, Dict, Union
from ..io.inputs.step import StepStringInput, StepInputs
from ..io.outputs.step import StepOutputs
from .run import RunStatus

class Results(List[Union[StepInputs, StepOutputs]]):
    
    @classmethod
    def from_runs(cls, runs: List[RunStatus]) -> 'Results':
        res = []

        for run in runs:
            row = [
                StepStringInput(
                    name='job-id',
                    description='The ID of the job that generated this run',
                    value=run.job_id,
                ),
                StepStringInput(
                    name='run-id',
                    description='The ID of the run this result row should be associated with',
                    value=run.id,
                ),
                StepStringInput(
                    name='run-status',
                    description='The stauts of the run this result row should be associated with',
                    value=run.status,
                ),
            ]

            row.extend(run.inputs)
            row.extend(run.outputs)

            res.append(row)
        
        return res