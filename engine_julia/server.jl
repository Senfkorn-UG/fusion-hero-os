function AnalyzeTimeSeries(history_vector)
# Berechne den gleitenden Durchschnitt der eudaimonistischen Dichte
    moving_avg = sum(history_vector) / length(history_vector)
    return moving_avg
end
