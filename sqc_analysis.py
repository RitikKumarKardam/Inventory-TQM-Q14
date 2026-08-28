from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt

ROOT=Path(__file__).resolve().parent
ART=ROOT/'artifacts'
ART.mkdir(exist_ok=True)

def pareto():
    df=pd.DataFrame({
        'Defect Type':['No clear return path','Module hidden from nav','Too many clicks','Shortcut unavailable','Breadcrumb absent','Inconsistent labels','Dashboard tile unclear','Other'],
        'Frequency':[14,10,8,6,5,3,2,2]
    }).sort_values('Frequency',ascending=False)
    df['Cumulative %']=df['Frequency'].cumsum()/df['Frequency'].sum()*100
    df.to_csv(ART/'defect_log.csv',index=False)
    fig,ax1=plt.subplots(figsize=(11,6)); x=range(len(df)); ax1.bar(list(x),df['Frequency']); ax1.set_ylabel('Defect Frequency'); ax1.set_xticks(list(x)); ax1.set_xticklabels(df['Defect Type'],rotation=35,ha='right',fontsize=8); ax1.set_title('Pareto Analysis - Navigation Defects')
    ax2=ax1.twinx(); ax2.plot(list(x),df['Cumulative %'],marker='o'); ax2.axhline(80,linestyle='--'); ax2.set_ylabel('Cumulative %'); ax2.set_ylim(0,110); fig.tight_layout(); fig.savefig(ART/'pareto_chart_reproducible.png',dpi=180); plt.close(fig)

if __name__=='__main__': pareto()
