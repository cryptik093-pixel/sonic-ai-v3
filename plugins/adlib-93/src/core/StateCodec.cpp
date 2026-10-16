#include "StateCodec.h"
#include <algorithm>
#include <charconv>
#include <cmath>
#include <iomanip>
#include <limits>
#include <map>
#include <sstream>
#include <stdexcept>
namespace adlib93 {
namespace {
struct Node { enum Kind{Null,Boolean,Number,String,Object,Array} kind=Null;bool boolean=false;double number=0;std::string text;std::map<std::string,Node> object;std::vector<Node> array; };
class Parser {
 const char* pos;const char* end;
 void ws(){while(pos!=end&&(*pos==' '||*pos=='\r'||*pos=='\n'||*pos=='\t'))++pos;}
 bool take(char c){ws();if(pos!=end&&*pos==c){++pos;return true;}return false;}
 [[noreturn]]void fail(){throw std::runtime_error("Malformed JSON");}
 unsigned hex(){unsigned n=0;for(int i=0;i<4;++i){if(pos==end)fail();char c=*pos++;n*=16;if(c>='0'&&c<='9')n+=unsigned(c-'0');else if(c>='a'&&c<='f')n+=unsigned(c-'a'+10);else if(c>='A'&&c<='F')n+=unsigned(c-'A'+10);else fail();}return n;}
 void utf8(std::string& out,unsigned cp){if(cp<128)out+=char(cp);else if(cp<2048){out+=char(192|(cp>>6));out+=char(128|(cp&63));}else if(cp<65536){out+=char(224|(cp>>12));out+=char(128|((cp>>6)&63));out+=char(128|(cp&63));}else{out+=char(240|(cp>>18));out+=char(128|((cp>>12)&63));out+=char(128|((cp>>6)&63));out+=char(128|(cp&63));}}
 std::string string(){if(!take('"'))fail();std::string out;while(pos!=end){unsigned char c=static_cast<unsigned char>(*pos++);if(c=='"')return out;if(c<32)fail();if(c!='\\'){out+=char(c);continue;}if(pos==end)fail();switch(*pos++){case '"':out+='"';break;case '\\':out+='\\';break;case '/':out+='/';break;case 'b':out+='\b';break;case 'f':out+='\f';break;case 'n':out+='\n';break;case 'r':out+='\r';break;case 't':out+='\t';break;case 'u':{auto cp=hex();if(cp>=0xd800&&cp<=0xdbff){if(end-pos<2||*pos++!='\\'||*pos++!='u')fail();auto low=hex();if(low<0xdc00||low>0xdfff)fail();cp=0x10000+((cp-0xd800)<<10)+(low-0xdc00);}else if(cp>=0xdc00&&cp<=0xdfff)fail();utf8(out,cp);break;}default:fail();}}fail();}
 Node value(unsigned depth){if(depth>32)fail();ws();if(pos==end)fail();Node n;
  if(*pos=='{'){++pos;n.kind=Node::Object;if(take('}'))return n;do{auto key=string();if(!take(':'))fail();if(!n.object.emplace(key,value(depth+1)).second)fail();}while(take(','));if(!take('}'))fail();return n;}
  if(*pos=='['){++pos;n.kind=Node::Array;if(take(']'))return n;do{n.array.push_back(value(depth+1));}while(take(','));if(!take(']'))fail();return n;}
  if(*pos=='"'){n.kind=Node::String;n.text=string();return n;}
  for(const auto& literal:{std::string("true"),std::string("false"),std::string("null")})if(static_cast<std::size_t>(end-pos)>=literal.size()&&std::string(pos,literal.size())==literal){pos+=literal.size();n.kind=literal=="null"?Node::Null:Node::Boolean;n.boolean=literal=="true";return n;}
  const char* begin=pos;if(*pos=='-')++pos;if(pos==end)fail();if(*pos=='0')++pos;else{if(*pos<'1'||*pos>'9')fail();while(pos!=end&&*pos>='0'&&*pos<='9')++pos;}
  if(pos!=end&&*pos=='.'){++pos;const auto* digits=pos;while(pos!=end&&*pos>='0'&&*pos<='9')++pos;if(pos==digits)fail();}
  if(pos!=end&&(*pos=='e'||*pos=='E')){++pos;if(pos!=end&&(*pos=='+'||*pos=='-'))++pos;const auto* digits=pos;while(pos!=end&&*pos>='0'&&*pos<='9')++pos;if(pos==digits)fail();}
  n.kind=Node::Number;const auto result=std::from_chars(begin,pos,n.number);if(result.ec!=std::errc{}||result.ptr!=pos||!std::isfinite(n.number))fail();return n;
 }
public: Parser(const void* data,std::size_t size):pos(static_cast<const char*>(data)),end(pos+size){}Node parse(){auto n=value(0);ws();if(pos!=end)fail();return n;}
};
const Node* field(const Node& n,const char* key){if(n.kind!=Node::Object)throw std::runtime_error("Expected object");auto it=n.object.find(key);return it==n.object.end()?nullptr:&it->second;}
double number(const Node& n){if(n.kind!=Node::Number)throw std::runtime_error("Expected number");return n.number;}
int integer(const Node& n,int low,int high){auto x=number(n);if(x!=std::floor(x)||x<low||x>high)throw std::runtime_error("Invalid integer");return static_cast<int>(x);}
bool boolean(const Node& n){if(n.kind!=Node::Boolean)throw std::runtime_error("Expected boolean");return n.boolean;}
ParameterSnapshot snapshot(const Node& node){auto s=makeInitSnapshot();for(std::size_t i=0;i<parameterCount;++i)if(const auto* p=field(node,parameterDefinitions()[i].id)){auto v=number(*p);const auto& d=parameterDefinitions()[i];if(v<d.min||v>d.max||((d.kind==ParameterKind::boolean||d.kind==ParameterKind::choice)&&v!=std::floor(v)))throw std::runtime_error("Parameter outside schema range");s.values[i]=static_cast<float>(v);}return persistentSnapshot(s);}
std::string quoted(const std::string& text){std::ostringstream o;o<<'"';for(unsigned char c:text){switch(c){case '"':o<<"\\\"";break;case '\\':o<<"\\\\";break;case '\n':o<<"\\n";break;case '\r':o<<"\\r";break;case '\t':o<<"\\t";break;default:if(c<32)o<<"\\u"<<std::hex<<std::setw(4)<<std::setfill('0')<<unsigned(c)<<std::dec;else o<<char(c);}}o<<'"';return o.str();}
void writeSnapshot(std::ostream& o,ParameterSnapshot s){s=persistentSnapshot(s);o<<'{';for(std::size_t i=0;i<parameterCount;++i){if(i)o<<',';o<<quoted(parameterDefinitions()[i].id)<<':'<<s.values[i];}o<<'}';}
}
std::string encodeStateJson(const PersistedState& state){
 std::ostringstream o;o.imbue(std::locale::classic());o<<std::setprecision(std::numeric_limits<float>::max_digits10);
 o<<"{\"schema\":1,\"parameters\":";writeSnapshot(o,state.parameters);
 if(state.hasPresetBaseline){o<<",\"presetBaseline\":";writeSnapshot(o,state.presetBaseline);}
 o<<",\"a\":";writeSnapshot(o,state.slots[0]);o<<",\"b\":";writeSnapshot(o,state.slots[1]);
 o<<",\"activeSlot\":"<<(state.activeSlot==1?1:0)<<",\"locks\":{\"input\":"<<(state.locks.input?"true":"false")<<",\"gate\":"<<(state.locks.gate?"true":"false")<<",\"output\":"<<(state.locks.output?"true":"false")<<"},\"ui\":{\"scale\":"<<(std::isfinite(state.ui.scale)?std::clamp(state.ui.scale,.75f,1.5f):1.f)<<",\"page\":"<<std::clamp(state.ui.page,0,5)<<",\"preset\":"<<quoted(state.ui.preset.substr(0,256))<<",\"modified\":"<<(state.ui.modified?"true":"false")<<"}}";
 return o.str();
}
std::vector<uint8_t> encodeStateBytes(const PersistedState& state){auto json=encodeStateJson(state);return {json.begin(),json.end()};}
DecodeResult decodeState(const void* data,std::size_t bytes){DecodeResult result;if(!data||!bytes||bytes>maximumStateBytes){result.error="State is empty or exceeds 256 KiB";return result;}try{const auto root=Parser(data,bytes).parse();if(auto p=field(root,"schema"))result.state.schema=integer(*p,1,1);if(auto p=field(root,"parameters"))result.state.parameters=snapshot(*p);
 if(auto p=field(root,"presetBaseline")){result.state.presetBaseline=snapshot(*p);result.state.hasPresetBaseline=true;}
 else result.state.presetBaseline=result.state.parameters;
 if(auto p=field(root,"a"))result.state.slots[0]=snapshot(*p);if(auto p=field(root,"b"))result.state.slots[1]=snapshot(*p);if(auto p=field(root,"activeSlot"))result.state.activeSlot=integer(*p,0,1);if(auto p=field(root,"locks")){if(auto q=field(*p,"input"))result.state.locks.input=boolean(*q);if(auto q=field(*p,"gate"))result.state.locks.gate=boolean(*q);if(auto q=field(*p,"output"))result.state.locks.output=boolean(*q);}if(auto p=field(root,"ui")){if(auto q=field(*p,"scale")){auto scale=number(*q);if(scale<.75||scale>1.5)throw std::runtime_error("Invalid UI scale");result.state.ui.scale=static_cast<float>(scale);}if(auto q=field(*p,"page"))result.state.ui.page=integer(*q,0,5);if(auto q=field(*p,"preset")){if(q->kind!=Node::String||q->text.size()>256)throw std::runtime_error("Invalid preset identity");result.state.ui.preset=q->text;}if(auto q=field(*p,"modified"))result.state.ui.modified=boolean(*q);}result.success=true;}catch(const std::exception& e){result.state=PersistedState{};result.error=e.what();}return result;}
}
