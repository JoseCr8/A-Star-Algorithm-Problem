#!/bin/sh
ulimit -t 120
python3 ASTARColaBus.py ./ASTAR-tests alumnos1.prob 1
python3 ASTARColaBus.py ./ASTAR-tests alumnos1.prob 2
python3 ASTARColaBus.py ./ASTAR-tests alumnos1.prob 3
python3 ASTARColaBus.py ./ASTAR-tests alumnos2.prob 1
python3 ASTARColaBus.py ./ASTAR-tests alumnos2.prob 2
python3 ASTARColaBus.py ./ASTAR-tests alumnos2.prob 3
python3 ASTARColaBus.py ./ASTAR-tests alumnos3.prob 1
python3 ASTARColaBus.py ./ASTAR-tests alumnos3.prob 2
python3 ASTARColaBus.py ./ASTAR-tests alumnos3.prob 3
python3 ASTARColaBus.py ./ASTAR-tests alumnos4.prob 1
python3 ASTARColaBus.py ./ASTAR-tests alumnos4.prob 2
python3 ASTARColaBus.py ./ASTAR-tests alumnos4.prob 3