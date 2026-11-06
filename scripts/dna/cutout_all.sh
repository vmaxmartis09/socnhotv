#!/bin/zsh
# Tách nền toàn bộ ảnh DNA -> characters/<id>/cutout/*.png (RGBA). Cần rembg[cpu,cli] (venv $RV).
cd /Volumes/Data/socnhotv
RV=${RV:-/private/tmp/claude-501/-Users-vmaxmartis--claude-spares-spare-dQdAyo/156a20e6-8b4e-4a99-af12-bc7538ef6276/scratchpad/rv}
C=data/projects/soc-nho-tv/characters
for id in soc_nho koala bac_voi co_huou_sao me_soc ong_de_rau_bac cho_lu de_bong de_mun meo_mimi; do
  src=$C/$id/dna; tmp=scratch/cut_in_$id; rm -rf $tmp; mkdir -p $tmp $C/$id/cutout
  if [ $id = soc_nho ]; then cp $C/$id/soc_nho_[0-9][0-9].png $tmp/; else cp $src/${id}_*.png $tmp/; fi
  $RV/bin/rembg p -m isnet-general-use -a -ae 8 $tmp $C/$id/cutout 2>&1 | tail -1
  echo "$id $(ls $C/$id/cutout | wc -l)"
done
echo CUT_DONE
