# Sondas da engenharia reversa

Estes scripts não são ferramenta de uso: são o **registro do método** que levou
ao `FORMATO.md`, guardados porque a técnica serve para o próximo formato binário
desconhecido.

O critério de aceite em todos é o mesmo e é falsificável: **consumir o arquivo
exatamente**. Um layout que sobra ou falta byte está errado, não "quase certo".

| | |
|---|---|
| `modprobe.py` | leitor cego: lê int32 e, quando o valor parece tamanho de string imprimível, consome como string. Revela o layout sem assumir nada. Foi o que mostrou que strings têm prefixo de tamanho |
| `probe17.py` | procura onde os registros começam num `filetype 17`, assumindo corpo igual ao 16 e exigindo consumo exato. **Falhou** — e a falha foi informativa: o início não era múltiplo de 4 |
| `probe17b.py` | força bruta de variantes de layout de registro (seção extra em cada posição, para cada tipo; campo extra antes/depois). Achou que o corpo do ft17 é idêntico ao do ft16 |
| `probe17c.py` | confirma a hipótese final do cabeçalho ft17 e imprime o "gap" não decodificado em hex |

O que custou tempo, para não repetir: ler `bool` como 4 bytes. O campo de 1 byte
dessincroniza o leitor no primeiro registro e o resto do arquivo vira lixo
aparente — dá a impressão de formato exótico onde não há.

E o que resolveu: parar de garimpar hex à mão e deixar o computador testar todos
os layouts candidatos.
