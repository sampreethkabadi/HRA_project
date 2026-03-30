# Project Description (goal/scientific or practical value):
The Cyberinfrastructure for Network Science Center (CNS, https://cns.iu.edu) at Indiana University utilizes Amazon CloudFront to log the usage of the Human Reference Atlas (HRA) Portal at https://humanatlas.io, see paper at  https://www.nature.com/articles/s41556-021-00788-6Links to an external site.. Amazon CloudFront allows tracking user interactions with websites. Datasets are available for download and downstream analysis and visualization. 


The HRA Registration User Interface (RUI) (see https://www.nature.com/articles/s42003-022-03644-xLinks to an external site.) is a web-deployed tool that allows users to indicate the spatial position, rotation, and scale of virtual tissue blocks in reference to the organs of the HRAoThe Exploration User Interface (EUI) enables users to view all the registered tissue blocks of the HRA in their spatial and semantic context. The Cell Distance Explorer (CDE) allows 2D and 3D visualization of cells for identifying cellular neighborhoods by type and cell-cell distance. 


In an effort to improve these UIs, our team implemented usage tracking via Amazon CloudFront. Specifically, we use website events to identify user actions. This is in addition to default logging values, such as user ID and timestamp. The goal of this project is to answer basic questions about HRA UI usage:


What is the distribution of frequency of user events? 
Which UI elements were used frequently and not frequently? 
How often was opacity changed in the RUI?
How often was spatial search used in the EUI? 
HoW often were the histograms and violin plots in the CDE downloaded? 


Answers to these questions will help guide future feature planning, user testing, and deployment. Further, it will help us detect where there is a lack of documentation, and where we need to more clearly make visible existing functionality that may be too hard to discover for our users. We would also be happy to hear the students’ proposed research questions. 