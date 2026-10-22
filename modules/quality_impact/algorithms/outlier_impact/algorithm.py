"""离群值扰动与清洗：对比原始 / 污染 / 删离群行 / 截断四种条件。"""

from modules.quality_impact.common import build_algorithm_run

run = build_algorithm_run('outlier', 'outlier_impact')
