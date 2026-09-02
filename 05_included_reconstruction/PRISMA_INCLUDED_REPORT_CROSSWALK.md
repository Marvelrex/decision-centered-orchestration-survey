# PRISMA Included-Report Reconstruction

## Corpus endpoint

The current survey dataset contains 83 unique cite keys. Each key is treated as one included report unless a version review proves otherwise.

| Analytical role | Included report keys |
|:--|--:|
| core_intervention | 39 |
| enabling_infrastructure | 8 |
| horizon_evidence | 9 |
| transfer_evidence | 27 |

## Intended discovery routes inherited from the survey

| Route | Included report keys | Confirmed in five-database exports | Near-title candidates | Not found |
|:--|--:|--:|--:|--:|
| database core route | 67 | 40 | 0 | 27 |
| supplementary route | 16 | 1 | 0 | 15 |

## Match status

- Confirmed by DOI or exact normalized title: 41
- Near-title candidates requiring manual confirmation: 0
- Not found in the five core exports: 42

A report that is not found in the five-database exports cannot be assigned to the database route without additional evidence. It may belong to the supplementary route, or it may reveal that the current database query does not reproduce the inherited corpus.

## Report-level crosswalk

| Cite key | Report title | Intended route | Role | Match | Sources | Flags |
|:--|:--|:--|:--|:--|:--|:--|
| `townend2019improving` | Improving data center efficiency through holistic scheduling in kubernetes | database core route | core_intervention | confirmed via verified title variant | IEEE Xplore | none |
| `rocha2019heats` | {Heats}: Heterogeneity-and energy-aware task-based scheduling | database core route | core_intervention | confirmed via exact normalized title | IEEE Xplore, Scopus, arXiv | none |
| `souza2024peaks` | {PEAKS}: Power Efficiency Aware {Kubernetes} Scheduler | database core route | horizon_evidence | not found via not found | Not found | gray_literature_candidate |
| `kumari2025npaks` | Real-Time Node's Power-Aware {Kubernetes} Scheduler in a Cloud Environment | database core route | core_intervention | confirmed via exact DOI | Scopus | none |
| `rattihalli2023fine` | Fine-grained heterogeneous execution framework with energy aware scheduling | database core route | core_intervention | confirmed via exact normalized title | IEEE Xplore, Scopus | none |
| `xu2014virtual` | A virtual data center deployment model based on the green cloud computing | database core route | transfer_evidence | not found via not found | Not found | none |
| `zhang2023carbon` | Carbon-efficient Virtual Machine Placement in Cloud Datacenters over Optical Networks | database core route | transfer_evidence | not found via not found | Not found | none |
| `coskun2008static` | Static and dynamic temperature-aware scheduling for multiprocessor SoCs | database core route | transfer_evidence | not found via not found | Not found | none |
| `menouer2021kcss` | {KCSS}: {Kubernetes} container scheduling strategy | database core route | core_intervention | confirmed via exact normalized title | Scopus | none |
| `zhou2015carbon` | Carbon-aware online control of geo-distributed cloud services | database core route | transfer_evidence | not found via not found | Not found | none |
| `radovanovic2022carbon` | Carbon-aware computing for datacenters | database core route | core_intervention | not found via not found | Not found | none |
| `hanafy2023carbonscaler` | {CarbonScaler}: Leveraging Cloud Workload Elasticity for Optimizing Carbon-Efficiency | database core route | core_intervention | confirmed via exact normalized title | ACM Digital Library, Scopus, arXiv | none |
| `ibm2024caspian` | {Caspian}: A Carbon-aware Workload Scheduler in Multi-Cluster {Kubernetes} Environments | database core route | core_intervention | confirmed via exact DOI | DBLP, IEEE Xplore, Scopus | none |
| `denToonder2024scale` | {S.C.A.L.E}: A {CO2}-Aware Scheduler for {OpenShift} at {ING} | database core route | core_intervention | confirmed via exact DOI | ACM Digital Library | none |
| `Microsoft2023` | Carbon-aware Computing: Measuring and Reducing the Carbon Intensity Associated with Software in Execution | database core route | enabling_infrastructure | not found via not found | Not found | gray_literature_candidate |
| `intel2024tas` | Telemetry Aware Scheduling (TAS) | database core route | enabling_infrastructure | not found via not found | Not found | gray_literature_candidate |
| `rothman2023rl` | An RL-Based Model for Optimized {Kubernetes} Scheduling | database core route | core_intervention | confirmed via exact normalized title | IEEE Xplore, Scopus | none |
| `espinosa2024optimizing` | Optimizing Energy Consumption of {Kubernetes} Clusters with Deep Reinforcement Learning | database core route | core_intervention | confirmed via exact DOI | Scopus | none |
| `hou2024eets` | {EETS}: An energy-efficient task scheduler in cloud computing based on improved DQN algorithm | database core route | transfer_evidence | not found via not found | Not found | none |
| `reddy2023energy` | An energy efficient {RL} based workflow scheduling in cloud computing | database core route | transfer_evidence | not found via not found | Not found | none |
| `iftikhar2023hunterplus` | {HunterPlus}: {AI} based energy-efficient task scheduling for cloud--fog computing environments | database core route | transfer_evidence | not found via not found | Not found | none |
| `malipatil2025energy` | Energy-Efficient Cloud Computing Through Reinforcement Learning-Based Workload Scheduling. | database core route | transfer_evidence | not found via not found | Not found | none |
| `raith2024opportunistic` | Opportunistic Energy-Aware Scheduling for Container Orchestration Platforms Using Graph Neural Networks | database core route | core_intervention | confirmed via exact normalized title | DBLP, IEEE Xplore, Scopus | none |
| `yang2024energy` | Energy-efficient {DAG} scheduling with {DVFS} for cloud data centers | database core route | transfer_evidence | not found via not found | Not found | none |
| `kaur2019keids` | {KEIDS}: Kubernetes-based energy and interference driven scheduler for industrial {IoT} in edge-cloud ecosystem | database core route | core_intervention | confirmed via exact normalized title | DBLP, IEEE Xplore, Scopus | none |
| `rao2024energy` | Energy-aware Scheduling Algorithm for Microservices in {Kubernetes} Clouds | database core route | core_intervention | confirmed via exact DOI | Scopus | none |
| `Jawaddi2025` | Analyzing Energy-Efficient and Kubernetes-Based Autoscaling of Microservices Using Probabilistic Model Checking | database core route | enabling_infrastructure | confirmed via exact normalized title | Scopus | none |
| `pradeep2025energy` | Energy-Optimized Scheduling for {AIoT} Workloads Using {TOPSIS} | database core route | core_intervention | confirmed via formal version preferred | IEEE Xplore, Scopus | preprint |
| `bellal20253gc` | {3GC}: A deadline-aware and energy-efficient resource allocation scheme for serverless edge computing | database core route | core_intervention | confirmed via exact normalized title | DBLP, IEEE Xplore, Scopus | none |
| `da2025foa` | {FOA-Energy}: A Multi-objective Energy-Aware Scheduling Policy for Serverless-based Edge-Cloud Continuum | database core route | core_intervention | confirmed via exact normalized title | ACM Digital Library, DBLP, Scopus | none |
| `ajmera2023energy` | Energy-efficient virtual machine scheduling in IaaS cloud environment using energy-aware green-particle swarm optimization | database core route | transfer_evidence | not found via not found | Not found | none |
| `kepler` | {Kepler}: A framework to calculate the energy consumption of containerized applications | database core route | enabling_infrastructure | confirmed via exact normalized title | IEEE Xplore, Scopus | none |
| `pijnacker2025container` | Container-level Energy Observability in {Kubernetes} Clusters | database core route | enabling_infrastructure | confirmed via formal version preferred | IEEE Xplore, Scopus | preprint |
| `11231033` | A Multi-Objective Framework for Power-Aware Scheduling in {Kubernetes} | database core route | core_intervention | confirmed via exact DOI | DBLP, IEEE Xplore, Scopus | none |
| `10.1145/3773274.3774276` | Energy-Aware Latency Optimization for Scheduling Serverless Workload in Edge Computing Environment | database core route | core_intervention | confirmed via exact DOI | ACM Digital Library, DBLP, Scopus | none |
| `11197392` | Energy-Aware Scheduling in Cloud-Native Environment | database core route | core_intervention | confirmed via exact DOI | IEEE Xplore, Scopus | none |
| `11101082` | Enhancing Energy Efficiency in {Kubernetes} Cluster Through Resource and Energy Aware Scheduling | database core route | core_intervention | confirmed via exact DOI | IEEE Xplore, Scopus | none |
| `10685327` | A Stable Matching Approach to Energy Efficient and Sustainable Serverless Scheduling for the Green Cloud Continuum | database core route | core_intervention | confirmed via exact DOI | DBLP | none |
| `ali2025experimentingenergyawarenessedgecloudcontainerized` | Experimenting with Energy-Awareness in Edge-Cloud Containerized Application Orchestration | database core route | core_intervention | confirmed via exact normalized title | DBLP, arXiv | preprint, gray_literature_candidate |
| `huang2023reducing` | Reducing Cloud Expenditures and Carbon Emissions via Virtual Machine Migration and Downsizing | database core route | transfer_evidence | not found via not found | Not found | none |
| `James2019ALC` | A Low Carbon {Kubernetes} Scheduler | database core route | core_intervention | confirmed via exact normalized title | DBLP, Scopus | none |
| `ghodsi2011dominant` | Dominant resource fairness: Fair allocation of multiple resource types | database core route | transfer_evidence | not found via not found | Not found | none |
| `8744199` | Ant Colony Algorithm for Multi-Objective Optimization of Container-Based Microservice Scheduling in Cloud | database core route | transfer_evidence | not found via not found | Not found | none |
| `ghafouri2023smart` | {Smart-Kube}: Energy-Aware and Fair {Kubernetes} Job Scheduler Using Deep Reinforcement Learning | database core route | core_intervention | confirmed via exact normalized title | DBLP, IEEE Xplore, Scopus | none |
| `9328612` | {DL2}: A Deep Learning-Driven Scheduler for Deep Learning Clusters | database core route | transfer_evidence | not found via not found | Not found | none |
| `MAIZX` | {MAIZX}: A Carbon-Aware Framework for Optimizing Cloud Computing Emissions | database core route | transfer_evidence | not found via not found | Not found | preprint, gray_literature_candidate |
| `gu2024greenflow` | {GreenFlow}: A Carbon-Efficient Scheduler for Deep Learning Workloads | database core route | transfer_evidence | not found via not found | Not found | none |
| `chadha2023greencourier` | {GreenCourier}: Carbon-Aware Scheduling for Serverless Functions | database core route | core_intervention | confirmed via exact normalized title | ACM Digital Library, DBLP, Scopus, arXiv | workshop |
| `cafe` | {CAFE}: Carbon-Aware Federated Learning in Geographically Distributed Data Centers | database core route | transfer_evidence | not found via not found | Not found | preprint |
| `cefl` | {EcoLearn}: Optimizing the Carbon Footprint of Federated Learning | database core route | transfer_evidence | not found via not found | Not found | none |
| `KEDA` | Implementation and Benchmarking of {Kubernetes} Horizontal Pod Autoscaling Method to Event-Driven Messaging System | database core route | enabling_infrastructure | not found via not found | Not found | none |
| `qi2024casa` | {CASA}: A Framework for SLO-and Carbon-Aware Autoscaling and Scheduling in Serverless Cloud Computing | database core route | core_intervention | confirmed via exact normalized title | DBLP, IEEE Xplore, Scopus | none |
| `serenari2024greenwhisk` | {GreenWhisk}: Emission-aware computing for serverless platform | database core route | core_intervention | not found via not found | Not found | none |
| `piontek2024carbon` | Carbon emission-aware job scheduling for {Kubernetes} deployments | database core route | core_intervention | confirmed via exact normalized title | DBLP, Scopus | none |
| `Souza_2023` | {CASPER}: Carbon-Aware Scheduling and Provisioning for Distributed Web Services | database core route | core_intervention | confirmed via exact DOI | ACM Digital Library | none |
| `lechowicz2025pcaps` | Carbon- and Precedence-Aware Scheduling for Data Processing Clusters | database core route | core_intervention | confirmed via formal version preferred | ACM Digital Library, Scopus | preprint, gray_literature_candidate |
| `kreutz2025budget` | Carbon-Aware Microservice Deployment for Optimal User Experience on a Budget | database core route | transfer_evidence | not found via not found | Not found | workshop, gray_literature_candidate |
| `guan2024u` | {U-DUCT}: Uncertainty-aware Dynamic Unified Carbon Modeling Tool for Datacenter Scheduling | database core route | enabling_infrastructure | not found via not found | Not found | none |
| `beena2025green` | A Green Cloud-Based Framework for Energy-Efficient Task Scheduling Using Carbon Intensity Data for Heterogeneous Cloud Servers | database core route | core_intervention | confirmed via exact normalized title | IEEE Xplore, Scopus | none |
| `rodrigues2025carbon` | Carbon-Aware Temporal Data Transfer Scheduling Across Cloud Datacenters | database core route | transfer_evidence | not found via not found | Not found | preprint |
| `11186459` | {GreenK8s}: Green-aware Scheduling for Sustainable {Kubernetes} Cluster Management | database core route | core_intervention | confirmed via exact DOI | DBLP, IEEE Xplore, Scopus | none |
| `chaudhary2026slaconstrainedcarbonawareroutinggeodistributed` | SLA-Constrained Carbon-Aware Routing in Geo-Distributed Serverless Clouds | database core route | core_intervention | confirmed via exact normalized title | DBLP | preprint, gray_literature_candidate |
| `huang2026greennessdrivenschedulingfaredge` | Greenness-Driven Scheduling in Far Edge {Kubernetes}: A {CODECO} Evaluation | database core route | core_intervention | confirmed via exact normalized title | arXiv | preprint, gray_literature_candidate |
| `7152842` | Water-Constrained Geographic Load Balancing in Data Centers | supplementary route | transfer_evidence | not found via not found | Not found | none |
| `7420641` | Exploiting Spatio-Temporal Diversity for Water Saving in Geo-Distributed Data Centers | supplementary route | transfer_evidence | not found via not found | Not found | none |
| `jiang2025waterwisecooptimizingcarbonwaterfootprint` | {WaterWise}: Co-optimizing Carbon- and Water-Footprint Toward Environmentally Sustainable Cloud Computing | supplementary route | transfer_evidence | not found via not found | Not found | preprint, gray_literature_candidate |
| `moore2025slit` | Sustainable Carbon-Aware and Water-Efficient {LLM} Scheduling in Geo-Distributed Cloud Datacenters | supplementary route | transfer_evidence | not found via not found | Not found | none |
| `moore2026marlin` | {MARLIN}: Multi-Agent Game-Theoretic Reinforcement Learning for Sustainable {LLM} Inference in Cloud Datacenters | supplementary route | transfer_evidence | confirmed via formal version preferred | ACM Digital Library | preprint |
| `li2024environmentallyequitableaigeographical` | Towards Environmentally Equitable {AI} via Geographical Load Balancing | supplementary route | transfer_evidence | not found via not found | Not found | preprint, gray_literature_candidate |
| `talukder2026balancingbitsdropsstressadjusted` | Balancing Bits and Drops: Stress-Adjusted Water Management for Data Centers | supplementary route | transfer_evidence | not found via not found | Not found | preprint, gray_literature_candidate |
| `wu2025waterconsumptionequalwater` | Not All Water Consumption Is Equal: A Water Stress Weighted Metric for Sustainable Computing | supplementary route | enabling_infrastructure | not found via not found | Not found | preprint, gray_literature_candidate |
| `10.1145/3373376.3378473` | Orbital Edge Computing: Nanosatellite Constellations as a New Class of Computer System | supplementary route | horizon_evidence | not found via not found | Not found | none |
| `9884906` | Benchmarking Deep Learning Inference of Remote Sensing Imagery on the Qualcomm Snapdragon And Intel Movidius Myriad X Processors Onboard the International Space Station | supplementary route | horizon_evidence | not found via not found | Not found | none |
| `wang2023satellitecomputingcasestudy` | Satellite Computing: A Case Study of Cloud-Native Satellites | supplementary route | horizon_evidence | not found via not found | Not found | preprint, gray_literature_candidate |
| `pfandzelter2025trabantserverlessarchitecturemultitenant` | {Trabant}: A Serverless Architecture for Multi-Tenant Orbital Edge Computing | supplementary route | horizon_evidence | not found via not found | Not found | preprint, gray_literature_candidate |
| `chen2026spacemoeorbitalgeneralintelligence` | {SpaceMoE}: Towards Orbital General Intelligence with Distributed Mixture-of-Experts Inference | supplementary route | horizon_evidence | not found via not found | Not found | preprint, gray_literature_candidate |
| `arcas2026futurespacebasedhighlyscalable` | Towards a future space-based, highly scalable {AI} infrastructure system design | supplementary route | horizon_evidence | not found via not found | Not found | preprint, gray_literature_candidate |
| `chen2026hotaicoldspace` | Hot {AI} in Cold Space: Thermal-Crosstalk-Aware Scheduling for Sustainable Orbital {AI} Clusters | supplementary route | horizon_evidence | not found via not found | Not found | preprint, gray_literature_candidate |
| `10.1007/978-3-031-26507-5_15` | Energy-Aware Placement of Network Functions in Edge-Based Infrastructures with Open Source MANO and Kubernetes | database core route | core_intervention | confirmed via exact normalized title | DBLP, Scopus | workshop |
| `carbonAwareKedaOperator` | {Carbon Aware {KEDA} Operator} | supplementary route | horizon_evidence | not found via not found | Not found | gray_literature_candidate |
| `dong2025towards` | Towards Performance and Energy Aware {Kubernetes} Scheduler | database core route | core_intervention | confirmed via exact DOI | ACM Digital Library | none |
| `10254745` | {GreenKube}: Towards Greener Container Orchestration using Artificial Intelligence | database core route | core_intervention | confirmed via exact DOI | IEEE Xplore, Scopus | none |
| `10.1007/978-3-032-19134-2_19` | {Kubernetes} Scheduling for Green-Powered Microgrid Data Centers | database core route | core_intervention | confirmed via exact DOI | DBLP, Scopus | none |

## Screening reconstruction boundary

The retained set is the current survey corpus, and screening was not duplicated. The ledger therefore supports a per-record audit of every decision. It does not support claims of independent dual screening or inter-rater agreement.

The database hit and duplicate counts can be reported from the export audit. Title and abstract exclusions can be calculated only after the duplicate review is frozen and every included report is assigned to a documented discovery route. Full-text exclusion counts cannot be invented when no historical exclusion ledger exists.
