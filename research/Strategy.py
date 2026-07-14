import numpy as np
import pandas as pd

def lin_reg(Y, X):
    X_array = np.asarray(X, dtype=float)
    Y_array = np.asarray(Y, dtype=float)
    X_const = np.column_stack((np.ones(len(X_array)), X_array))
    coeffs, _, _, _ = np.linalg.lstsq(X_const, Y_array, rcond=None)
    alpha, beta = coeffs
    residuals = Y_array - (alpha + beta * X_array)
    if hasattr(Y, "index"):
        return alpha, beta, pd.Series(residuals, index=Y.index)
    return alpha, beta, residuals

def z_score(residuals, window=None):
    if window:
        mean = residuals.rolling(window=window).mean()
        std = residuals.rolling(window=window).std()
    else:
        mean = residuals.mean()
        std = residuals.std()
    zscore = (residuals - mean)/std
    return zscore 
    
def generate_signals(zscore, entry_threshold=2.5, exit_threshold=0.5):
    if exit_threshold >= entry_threshold:
        raise ValueError("exit_threshold must be smaller than entry_threshold")

    position = 0
    signals = pd.Series(index=zscore.index, dtype='int')

    for date, value in zscore.items():
        if position == 0:
            if value > entry_threshold:
                position = -1
            elif value < -entry_threshold:
                position = 1
        elif position == 1 and value >= -exit_threshold:
            position = 0
        elif position == -1 and value <= exit_threshold:
            position = 0

        signals.at[date] = position

    return signals
