# Repo Analysis: ProphitBet

Role: `Oracle`
URL: https://github.com/kochlisGit/ProphitBet-Soccer-Bets-Predictor.git

## ML and Data Signals
- Signals: keras, numpy, optuna, pandas, scikit-learn, sklearn, tensorflow, xgboost
- Notebooks: False
- Data dir: False

## Integration Signals (top files)
- src\gui\windows\models\fixtures.py (score 3)
- src\gui\windows\leagues\new.py (score 2)
- src\gui\windows\models\evaluator.py (score 2)
- src\gui\windows\models\predictor.py (score 2)

## Prompt and Persona Definitions (hits)
- `README.md`
  - Excerpt: `all -r requirements.txt`.\n\nIf you are a new user, you can use the `install.py` script to automatically download the required libraries. Open the Command Line (CMD) (or Trminal in Linux). In windows, you can open the cmd by typing *cmd* or *Command Prompt* in the windows search bar or by pressing the keys *Win+R* and typing *cmd* there. Then, nagivate on the created folder (e.g., *cd Downloads/ProphitBet*. Finally, type: `python install.py` and press ENTER to initiate the installation. These librarie`
- `src\gui\windows\models\evaluator.py`
  - Excerpt: `ip(tooltip_2)\n        self._slider_percentile_under.setToolTip(tooltip_u)\n        self._slider_percentile_over.setToolTip(tooltip_o)\n\n    def _show_instructions(self):\n        QMessageBox.information(\n            self,\n            'Evaluation Instructions',\n            'Select the target type, model and the dataset you wish to evaluate.'\n            'You can also specify odd-range and probability percentile filters to utilize during predictions.'\n            'The filters will not change the model`
- `src\gui\windows\models\trainer.py`
  - Excerpt: `f, model: ClassificationModel, model_config: Dict[str, Any]):\n        self._model_db.save_model(model=model, model_config=model_config)\n\n    def _show_instructions(self):\n        QMessageBox.information(\n            self,\n            'Training Instructions',\n            'Select the model hyperparameters and press "Train".'\n            'If you don\'t know which hyperparameters to choose, enable "Tune" and set trials and objective (metric to maximize). '\n            'Finally check the hyperparameters`

Unk = Uncle
Target: 35+ users
