CREATE TABLE research_papers (
  id text PRIMARY KEY, title text NOT NULL, venue text NOT NULL, year integer NOT NULL,
  topic text NOT NULL, abstract text NOT NULL, source_url text NOT NULL
);
INSERT INTO research_papers(id,title,venue,year,topic,abstract,source_url) VALUES
('otc-ingredients','Risk of unintentional overdose with non-prescription acetaminophen products','J Gen Intern Med',2012,'用药核对','通过成人模拟服药任务研究非处方产品用量和重复成分理解。提示产品记录和成分核对具有研究价值，不能将其样本结果直接当成本项目人群的误用率。','https://pubmed.ncbi.nlm.nih.gov/22638604/'),
('respiratory-trajectories','Post-consultation acute respiratory tract infection recovery: a latent class-informed analysis of individual patient data','Br J Gen Pract',2023,'连续观察','基于个体数据分析呼吸道感染咨询后的恢复轨迹，关注不同变化过程。当前产品只做实际评分的描述性对照，不复现论文的潜在类别方法。','https://pubmed.ncbi.nlm.nih.gov/36823057/'),
('healthbench','HealthBench: Evaluating Large Language Models Towards Improved Human Health','arXiv 预印本',2025,'对话评估','使用多轮健康对话及医师编写的对话专属标准，评价模型表现。可参考其准确性、上下文与沟通维度设计本项目评估，不把通用基准成绩当作本产品临床性能。','https://arxiv.org/abs/2505.08775'),
('decentralized-monitoring','Longitudinal voice monitoring in a decentralized Bring Your Own Device trial for respiratory illness detection','npj Digital Medicine',2025,'院外数据','去中心化研究结合个人设备的连续观察与呼吸道疾病检测，展示院外纵向数据的研究方式。本项目未接入声音或客观检测，也不据此宣称感染识别能力。','https://www.nature.com/articles/s41746-025-01584-4');
