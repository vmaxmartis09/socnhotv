#!/bin/zsh
cd /Volumes/Data/socnhotv
# id:số ảnh (phụ=5, chính khác Bi=7). Tự xoay tài khoản Gemini (authuser 0<->1) khi hết hạn mức.
AUTHF=scratch/auth; [ -f $AUTHF ] || echo 0 > $AUTHF
for spec in koala:5 bac_voi:5 co_huou_sao:5 me_soc:5 ong_de_rau_bac:5 cho_lu:7 de_bong:7 de_mun:7 meo_mimi:7; do
  c=${spec%%:*}; T=${spec##*:}
  for pass in 1 2 3 4 5 6 7 8; do
    n=$(ls data/projects/soc-nho-tv/characters/$c/dna/ 2>/dev/null | wc -l | tr -d ' ')
    [ "$n" -ge "$T" ] && break
    from=$((n>0 ? n+1 : 1)); A=$(cat $AUTHF)
    sed "s/__CHAR__/$c/;s/__FROM__/$from/;s/__TO__/$T/;s/__AUTH__/$A/" scripts/dna/gen_dna.mjs > scratch/run_$c.mjs
    echo "== $c pass $pass (have $n/$T) authuser=$A"
    ego-browser nodejs < scratch/run_$c.mjs 2>&1 | tee scratch/last_pass.log
    if grep -q "Hạn mức\|giới hạn của bạn" scratch/last_pass.log; then echo $((1-A)) > $AUTHF; echo "-- hết hạn mức, đổi sang authuser=$((1-A))"; fi
  done
done
echo ALL_DONE
