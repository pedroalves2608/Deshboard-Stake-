from pathlib import Path
from datetime import datetime
import shutil

# Ajuste aqui se o nome do seu CSV principal for diferente
BASE_DIR = Path(__file__).resolve().parent
CSV_ATUAL = BASE_DIR / "data" / "output" / "frequencia_estaca_2025.csv"

# Pasta onde você quer guardar as versões semanais
PASTA_SNAPSHOTS = BASE_DIR / "data" / "Historico"
PASTA_SNAPSHOTS.mkdir(parents=True, exist_ok=True)

def main():
    if not CSV_ATUAL.exists():
        raise FileNotFoundError(f"CSV principal não encontrado: {CSV_ATUAL}")

    # Nomeia com data e hora para nunca sobrescrever
    stamp = datetime.now().strftime("%Y-%m-%d_%H%M")
    destino = PASTA_SNAPSHOTS / f"frequencia_estaca_2025_{stamp}.csv"

    shutil.copy2(CSV_ATUAL, destino)
    print(f"Snapshot criado: {destino}")

if __name__ == "__main__":
    main()
