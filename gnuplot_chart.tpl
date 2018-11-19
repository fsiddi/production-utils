set terminal pngcairo transparent enhanced font "arial,10" fontscale 1.0 size 2048, 858
set output '{tmp_chart_file}'
set key autotitle columnhead


set multiplot
set size 1, 0.5

set border lt 4
set origin 0.0,0.5
set yrange [0:*]
plot '{frames_stats_file}' using 1:3 with lines lt 4

set origin 0.0,0.0
plot '{frames_stats_file}' using 1:4 with lines lt 4

unset multiplot

# set xtics in
#unset xtics
#set border "white"
#plot 'data.dat' with lines

