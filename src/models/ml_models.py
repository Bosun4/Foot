from sklearn.ensemble import RandomForestClassifier
from sklearn.neural_network import MLPClassifier
import xgboost as xgb
import joblib
import pandas as pd

def train_ml_models(df_historical):
    # 特征工程（你已有历史数据时用）
    features = ['home_form', 'away_form', 'h2h', 'league_strength']  # 自行扩展
    X = df_historical[features]
    y = df_historical['result']  # 0=负 1=平 2=胜
    
    rf = RandomForestClassifier(n_estimators=200, random_state=42)
    xgb_model = xgb.XGBClassifier(n_estimators=300, learning_rate=0.05)
    mlp = MLPClassifier(hidden_layer_sizes=(100,50), max_iter=500)
    
    rf.fit(X, y)
    xgb_model.fit(X, y)
    mlp.fit(X, y)
    
    joblib.dump(rf, 'src/models/rf.pkl')
    joblib.dump(xgb_model, 'src/models/xgb.pkl')
    joblib.dump(mlp, 'src/models/mlp.pkl')
    return rf, xgb_model, mlp