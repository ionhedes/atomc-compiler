struct Pt{
	int x;
	int y;
	};
struct Pt points[5];

double max(double a, double b){
	if(a>b)return a;
		else return b;
	}

int len(char s[]){
	int i;
	i=0;
	while(s[i])i=i+1;
	return i;
	}

void main(){
	int i;
	for(i=10;;i=i+4){
		puti(i);
		if(i==0)break;

	}
}
	