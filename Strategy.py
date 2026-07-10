import numpy as np
import pandas as pd

"""Uses linear regression to obtain residuals, alpha, and beta values."""
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

"""Uses spread residuals found from linear regression to compute z-score"""
def z_score(residuals, window=None):
    if window:
        mean = residuals.rolling(window=window).mean()
        std = residuals.rolling(window=window).std()
    else:
        mean = residuals.mean()
        std = residuals.std()
    zscore = (residuals - mean)/std
    return zscore 
    
"""Calculates short and long signals using z-score"""
def generate_signals(zscore):
    signals = pd.Series(index=zscore.index, dtype='int')
    signals[zscore > 0.5] = 1   #Short A, Long B
    signals[zscore < -0.5] = -1 #Short B, Long A
    signals[(zscore >= -0.5) & (zscore <= 0.5)] = 0   #Neutral, close the position
    return signals    
