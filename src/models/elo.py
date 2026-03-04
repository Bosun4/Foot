def update_elo(home_elo, away_elo, result, k=32, home_adv=100):
    expected_home = 1 / (1 + 10**((away_elo - home_elo - home_adv)/400))
    if result == 'home': score = 1
    elif result == 'draw': score = 0.5
    else: score = 0
    new_home = home_elo + k * (score - expected_home)
    new_away = away_elo - k * (score - expected_home)
    return new_home, new_away