# MillikanCVV1

This work evaluates the integration of computer vision into the Millikan oil-drop experiment—an experiment that played a pivotal role in R.A. Millikan’s receipt of the Nobel Prize in Physics in 1923 [[1]](#1)—and introduces a minimally viable user interface to assess its impact on usability in an educational context.

Millikan’s experiment involved observing tiny oil droplets suspended in a chamber between two electrically charged plates. Using a microscope, he measured the velocity of the droplets as they fell under gravity and as they rose in response to an electric field. By varying the electric field and observing changes in the droplets’ motion, he was able to determine their charge. He accounted for factors such as air viscosity, drop density, and the effects of small drop size using corrections to Stokes's law. Millikan controlled the experimental conditions to eliminate errors from convection currents and pressure variations. This precise approach allowed him to determine that the charges on the oil droplets were multiples of a fundamental unit, confirming the quantized nature of electric charge [[2]](#2).

For over six decades, the Millikan oil-drop experiment has been a cornerstone in the pedagogy and practice of experimental physics, serving as a critical tool for illustrating the quantization of electric charge and the measurement of fundamental physical constants [[2]](#2), [[3]](#3), [[4]](#4), [[5]](#5). 
Despite its enduring significance, the traditional execution of this experiment in academic laboratories remains encumbered by inefficiencies [[6]](#6), [[7]](#7), [[8]](#8), [[9]](#9), [[10]](#10), [[11]](#11). These inefficiencies largely stem from the reliance on antiquated software and the necessity for manual data recording and processing, typically involving the laborious entry of observational data into basic spreadsheet programs \cite{making_it_worthwhile}. This technological lag not only hampers the accurate and efficient execution of academic experiments but also deprives students of an immersive engagement \cite{making_it_worthwhile}, with what has been lauded as one of the most elegant and profound demonstrations in the realm of physical sciences. 

To address this challenge, we propose an updated methodology that combines modern computer vision algorithms with a minimally viable user interface designed to enhance usability. 

# Requirements

**Python 3.12.1**

# Steps

1. Create Environment

```sh
python -m venv venv
```

2. Source Virtual Environment


```sh
## Powershell 

.\venv\Scripts\Activate.ps1
```

```sh
## Mac 

source venv/bin/activate
```

3. Install Requirements
```sh
pip install -r requirements.txt
```

4. Run Tool

```sh
python annotationTool.py
```

4 Building the Excutable (**Optional**)
```sh
pyinstaller.exe --onefile --noconsole --icon=images\experiment_105162.ico  --clean annotationTool.py
```


## References
<a id="1">[1]</a> 
he Nobel Prize in Physics 1923, https://www.nobelprize.org/prizes/physics/1923/summary/

<a id="2">[2]</a> 
Millikan., R.A.: On the Elementary Electrical Charge and the Avogadro Constant. Physical Review 2(2), 109–143 (Aug 1913). https://doi.org/10.1103/PhysRev.2.109, https://link.aps.org/doi/10.1103/PhysRev.2.109

<a id="3">[3]</a> 
Rodríguez, M., Niaz, M.: The Oil Drop Experiment: An Illustration of Scientific Research Methodology and its Implications for Physics Textbooks. Instructional Science 32, 357–386 (Sep 2004). https://doi.org/10.1023/B:TRUC.0000044641.19894.
ed

<a id="4">[4]</a> 
Niaz, M.: The Oil Drop Experiment: A Rational Reconstruction of the Millikan-Ehrenhaft Controversy and Its Implications for Chemistry Textbooks. Journal of Research in Science Teaching 37(5), 480–508 (May 2000). https: //doi.org/10.1002/(SICI)1098-2736(200005)37:5<480::AID-TEA6>3.0.CO;2-X, https://onlinelibrary.wiley.com/doi/10.1002/(SICI)1098-2736(200005)37:5<480::AID-TEA6>3.0.CO;2-X

<a id="5">[5]</a> 
Crease, R.P.: The most beautiful experiment. Physics World 15(9), 19 (Sep 2002). https://doi.org/10.1088/2058-7058/15/9/22, https://dx.doi.org/10.1088/2058-7058/15/9/22

<a id="6">[6]</a> 
Klassen, S.: Identifying and Addressing Student Difficulties with the Millikan Oil Drop Experiment. Science & Education 18(5), 593–607 (May 2009). https://doi.org/10.1007/s11191-007-9126-2, https://doi.org/10.1007/s11191-007-9126-2

<a id="7">[7]</a> 
 Silva, K.J., Mahendra, J.C.: Digital video microscopy in the Millikan oil-drop experiment. American Journal of Physics 73(8), 789–792 (Aug 2005). https://doi.org/10.1119/1.1848112, https://pubs.aip.org/ajp/article/73/8/789/1056216/Digital-video-microscopy-in-the-Millikan-oil-drop

<a id="8">[8]</a> 
 Li, Y., Su, G., Pan, H., Tan, C., Li, G.: Programming experiment course for innovative and sustainable education: A case study of Java for Millikan Oil Drop experiment. Journal of Cleaner Production 447, 141569 (Apr 2024). https://doi.org/10.1016/j.jclepro.2024.141569, https://www.sciencedirect.com/science/article/pii/S0959652624010175

<a id="9">[9]</a>
 Hogan, B., Hasbun, J.: The Millikan Oil Drop Experiment: A Simulation Suitable For Classroom Use. Georgia journal of science XX, XX–XX (2016), https://www.semanticscholar.org/paper/The-Millikan-Oil-Drop-Experiment%3A-A-Simulation-For-Hogan-Hasbun/bf7c8742b417fb2db9a6e20aef85f4dd7b7c0891\

<a id="10">[10]</a>
 Jones, R.C.: The Millikan oil-drop experiment: Making it worthwhile. American Journal of Physics 63(11), 970–977 (Nov 1995). https://doi.org/10.1119/1.18001, https://pubs.aip.org/ajp/article/63/11/970/1041326/The-Millikan-oil-drop-experiment-Making-it

<a id="11">[11]</a>
 Klassen, S.: The Pedagogical Renewal of the Millikan Oil Drop Experiment