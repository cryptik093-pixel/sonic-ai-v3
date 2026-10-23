#include "omega/Preset.h"
#include <algorithm>
#include <charconv>
#include <iomanip>
#include <locale>
#include <set>
#include <sstream>
#include <stdexcept>

namespace omega {
namespace {
class Reader {
    std::string_view s; size_t p=0;
public:
    explicit Reader(std::string_view text):s(text) {if(s.size()>65536) fail("Patch exceeds 64 KiB");}
    [[noreturn]] void fail(const char* message) {throw std::runtime_error(message);}
    void ws(){while(p<s.size()&&(s[p]==' '||s[p]=='\n'||s[p]=='\r'||s[p]=='\t'))++p;}
    bool take(char c){ws();if(p<s.size()&&s[p]==c){++p;return true;}return false;}
    void need(char c){if(!take(c))fail("Invalid JSON structure");}
    bool end(){ws();return p==s.size();}
    unsigned hex4(){unsigned n=0;for(int k=0;k<4;++k){if(p==s.size())fail("Truncated Unicode escape");const char c=s[p++];n*=16;if(c>='0'&&c<='9')n+=c-'0';else if(c>='a'&&c<='f')n+=c-'a'+10;else if(c>='A'&&c<='F')n+=c-'A'+10;else fail("Invalid Unicode escape");}return n;}
    void utf8(std::string& out,unsigned c){if(c<0x80)out+=char(c);else if(c<0x800){out+=char(0xc0|(c>>6));out+=char(0x80|(c&63));}else if(c<0x10000){out+=char(0xe0|(c>>12));out+=char(0x80|((c>>6)&63));out+=char(0x80|(c&63));}else{out+=char(0xf0|(c>>18));out+=char(0x80|((c>>12)&63));out+=char(0x80|((c>>6)&63));out+=char(0x80|(c&63));}}
    std::string text(){need('"');std::string out;bool closed=false;
        while(p<s.size()){unsigned char c=static_cast<unsigned char>(s[p++]);if(c=='"'){closed=true;break;}if(c<32)fail("Control character in JSON string");if(c!='\\'){out+=char(c);continue;}
            if(p==s.size())fail("Truncated JSON escape");switch(s[p++]){case '"':out+='"';break;case '\\':out+='\\';break;case '/':out+='/';break;case 'b':out+='\b';break;case 'f':out+='\f';break;case 'n':out+='\n';break;case 'r':out+='\r';break;case 't':out+='\t';break;case 'u':{unsigned u=hex4();if(u>=0xd800&&u<=0xdbff){if(p+2>s.size()||s[p]!='\\'||s[p+1]!='u')fail("Missing low surrogate");p+=2;unsigned low=hex4();if(low<0xdc00||low>0xdfff)fail("Invalid low surrogate");u=0x10000+((u-0xd800)<<10)+(low-0xdc00);}else if(u>=0xdc00&&u<=0xdfff)fail("Unexpected low surrogate");utf8(out,u);break;}default:fail("Invalid JSON escape");}}
        if(!closed)fail("Unterminated JSON string");return out;}
    double number(){ws();const auto start=p;if(p<s.size()&&s[p]=='-')++p;if(p==s.size())fail("Missing number");if(s[p]=='0')++p;else{if(s[p]<'1'||s[p]>'9')fail("Expected number");while(p<s.size()&&s[p]>='0'&&s[p]<='9')++p;}
        if(p<s.size()&&s[p]=='.'){++p;const auto begin=p;while(p<s.size()&&s[p]>='0'&&s[p]<='9')++p;if(p==begin)fail("Missing fractional digits");}
        if(p<s.size()&&(s[p]=='e'||s[p]=='E')){++p;if(p<s.size()&&(s[p]=='+'||s[p]=='-'))++p;const auto begin=p;while(p<s.size()&&s[p]>='0'&&s[p]<='9')++p;if(p==begin)fail("Missing exponent");}
        double value=0;auto result=std::from_chars(s.data()+start,s.data()+p,value);if(result.ec!=std::errc{}||result.ptr!=s.data()+p||!std::isfinite(value))fail("Invalid finite number");return value;}
    template<class F> void object(F fn){need('{');std::set<std::string> seen;if(take('}'))return;do{auto key=text();if(!seen.insert(key).second)fail("Duplicate object key");need(':');fn(key);}while(take(','));need('}');}
    void length(const std::string& text,size_t low,size_t high){size_t count=0;
        for(size_t i=0;i<text.size();){unsigned char c=static_cast<unsigned char>(text[i++]);unsigned u=c;int extra=0;if(c>=0xc2&&c<=0xdf){u=c&31;extra=1;}else if(c>=0xe0&&c<=0xef){u=c&15;extra=2;}else if(c>=0xf0&&c<=0xf4){u=c&7;extra=3;}else if(c>=128)fail("Invalid UTF-8");
            for(int j=0;j<extra;++j){if(i==text.size())fail("Truncated UTF-8");unsigned char b=static_cast<unsigned char>(text[i++]);if((b&0xc0)!=0x80)fail("Invalid UTF-8 continuation");u=(u<<6)|(b&63);}
            if((extra==1&&u<128)||(extra==2&&u<2048)||(extra==3&&u<65536)||u>0x10ffff||(u>=0xd800&&u<=0xdfff))fail("Invalid Unicode scalar");++count;}
        if(count<low||count>high)fail("Patch text length outside schema");}
};
std::string quoted(const std::string& text){std::string out="\"";constexpr char hex[]="0123456789abcdef";for(unsigned char c:text){switch(c){case '"':out+="\\\"";break;case '\\':out+="\\\\";break;case '\n':out+="\\n";break;case '\r':out+="\\r";break;case '\t':out+="\\t";break;default:if(c<32){out+="\\u00";out+=hex[c>>4];out+=hex[c&15];}else out+=char(c);}}return out+'"';}
}
bool parsePreset(std::string_view document,Preset& result,std::string& error){
    try{Reader r(document);Preset candidate;std::set<std::string> required;
        r.object([&](const std::string& key){required.insert(key);
            if(key=="schema_version"){if(r.number()!=1)r.fail("Unsupported patch schema");}
            else if(key=="instrument"){if(r.text()!="omega-sonic-organism")r.fail("Wrong instrument");}
            else if(key=="name"){candidate.name=r.text();r.length(candidate.name,1,80);}
            else if(key=="author"){candidate.author=r.text();r.length(candidate.author,1,80);}
            else if(key=="description"){candidate.description=r.text();r.length(candidate.description,0,400);}
            else if(key=="tags"){r.need('[');std::set<std::string> seen;if(!r.take(']')){do{auto tag=r.text();r.length(tag,0,30);if(!seen.insert(tag).second)r.fail("Duplicate tag");candidate.tags.push_back(tag);if(candidate.tags.size()>12)r.fail("Too many tags");}while(r.take(','));r.need(']');}}
            else if(key=="params"){std::array<bool,parameterDefinitions.size()> supplied{};r.object([&](const std::string& name){int index=-1;for(size_t i=0;i<parameterDefinitions.size();++i)if(name==parameterDefinitions[i].key)index=int(i);if(index<0)r.fail("Unknown patch parameter");double n=r.number();if(n<0||n>1)r.fail("Parameter outside 0..1");const int steps=parameterDefinitions[size_t(index)].steps;if(steps&&std::abs(n-std::round(n*steps)/steps)>1e-12)r.fail("Invalid discrete parameter");candidate.params[size_t(index)]=n;supplied[size_t(index)]=true;});for(size_t i=0;i<6;++i)if(!supplied[i])r.fail("Missing principal parameter");}
            else r.fail("Unknown patch property");});
        for(const auto* key:{"schema_version","instrument","name","author","params"})if(!required.count(key))r.fail("Missing patch property");
        if(!r.end())r.fail("Trailing JSON data");result=std::move(candidate);error.clear();return true;
    }catch(const std::exception& ex){error=ex.what();return false;}
}
std::string exportPreset(const Preset& p){std::ostringstream out;out.imbue(std::locale::classic());out<<std::setprecision(17)<<"{\n  \"schema_version\":1,\n  \"instrument\":\"omega-sonic-organism\",\n  \"name\":"<<quoted(p.name)<<",\n  \"author\":"<<quoted(p.author)<<",\n  \"description\":"<<quoted(p.description)<<",\n  \"tags\":[";for(size_t i=0;i<p.tags.size();++i){if(i)out<<',';out<<quoted(p.tags[i]);}out<<"],\n  \"params\":{\n";const size_t count=(p.params[15]!=0||p.params[16]!=0||p.params[17]!=0)?p.params.size():15;for(size_t i=0;i<count;++i){if(i)out<<",\n";out<<"    "<<quoted(parameterDefinitions[i].key)<<':'<<p.params[i];}out<<"\n  }\n}\n";return out.str();}
}
