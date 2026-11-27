package org.padtv.bridge.tools;
import org.objectweb.asm.*;
import org.objectweb.asm.tree.*;
import org.objectweb.asm.tree.analysis.*;
import java.nio.file.*;
import java.util.*;
import java.util.zip.*;
import java.io.*;
/** Strict DEX constructor-elision adapter. No verifier suppression or app matching.
 * Android permits new C followed by an ancestor constructor after constructor
 * elision. JVM needs a constructor at every direct-super step. Repair only
 * when every skipped constructor is absent; never bypass an existing body.
 */
public final class ConstructorRepair {
 static final class Header {String parent;Set<String> constructors=new HashSet<>();Header(ClassNode n){parent=n.superName;for(MethodNode m:n.methods)if(m.name.equals("<init>"))constructors.add(m.desc);}}
 static final class Origins extends SourceInterpreter {
  Origins(){super(Opcodes.ASM9);}
  @Override public SourceValue copyOperation(AbstractInsnNode instruction,SourceValue value){return value;}
 }
 static ClassNode node(byte[] data,int flags){ClassNode n=new ClassNode();new ClassReader(data).accept(n,flags);return n;}
 static byte[] read(ZipFile file,ZipEntry entry)throws IOException{try(InputStream stream=file.getInputStream(entry)){return stream.readAllBytes();}}
 static List<String> chain(Map<String,Header> headers,String child,String ancestor,String descriptor){
  List<String> path=new ArrayList<>();Set<String> visited=new HashSet<>();
  while(!child.equals(ancestor)){Header h=headers.get(child);if(h==null||h.constructors.contains(descriptor)||!visited.add(child)||path.size()>=64)return null;path.add(child);child=h.parent;if(child==null)return null;}
  return path.isEmpty()?null:path;
 }
 static MethodNode bridge(String parent,String descriptor){
  MethodNode method=new MethodNode(Opcodes.ACC_PUBLIC|Opcodes.ACC_SYNTHETIC,"<init>",descriptor,null,null);
  method.instructions.add(new VarInsnNode(Opcodes.ALOAD,0));int local=1;
  for(Type t:Type.getArgumentTypes(descriptor)){method.instructions.add(new VarInsnNode(t.getOpcode(Opcodes.ILOAD),local));local+=t.getSize();}
  method.instructions.add(new MethodInsnNode(Opcodes.INVOKESPECIAL,parent,"<init>",descriptor,false));method.instructions.add(new InsnNode(Opcodes.RETURN));method.maxLocals=local;method.maxStack=local;return method;
 }
 public static void main(String[] args)throws Exception{
  Map<String,Header> headers=new HashMap<>();Map<String,byte[]> changed=new HashMap<>();Map<String,Set<String>> bridges=new HashMap<>();int repaired=0;
  try(ZipFile input=new ZipFile(args[0])){
   List<? extends ZipEntry> entries=Collections.list(input.entries());
   for(ZipEntry entry:entries)if(entry.getName().endsWith(".class")){ClassNode n=node(read(input,entry),ClassReader.SKIP_CODE|ClassReader.SKIP_DEBUG|ClassReader.SKIP_FRAMES);headers.put(n.name,new Header(n));}
   for(ZipEntry entry:entries){if(!entry.getName().endsWith(".class"))continue;ClassNode cls=node(read(input,entry),ClassReader.SKIP_DEBUG|ClassReader.SKIP_FRAMES);boolean dirty=false;
    for(MethodNode method:cls.methods){Set<String> allocated=new HashSet<>();for(AbstractInsnNode instruction:method.instructions)if(instruction.getOpcode()==Opcodes.NEW)allocated.add(((TypeInsnNode)instruction).desc);
     boolean candidate=false;for(AbstractInsnNode instruction:method.instructions)if(instruction instanceof MethodInsnNode){MethodInsnNode call=(MethodInsnNode)instruction;if(call.getOpcode()==Opcodes.INVOKESPECIAL&&call.name.equals("<init>"))for(String name:allocated){if(chain(headers,name,call.owner,call.desc)!=null){candidate=true;break;}}}
     if(!candidate)continue;Frame<SourceValue>[] frames=new Analyzer<SourceValue>(new Origins()).analyze(cls.name,method);int index=0;
     for(AbstractInsnNode instruction:method.instructions){Frame<SourceValue> frame=frames[index++];if(!(instruction instanceof MethodInsnNode)||frame==null)continue;MethodInsnNode call=(MethodInsnNode)instruction;if(call.getOpcode()!=Opcodes.INVOKESPECIAL||!call.name.equals("<init>"))continue;
      int receiver=frame.getStackSize()-Type.getArgumentTypes(call.desc).length-1;if(receiver<0)throw new IllegalArgumentException("Invalid constructor stack");SourceValue value=frame.getStack(receiver);if(value.insns.size()!=1)continue;AbstractInsnNode origin=value.insns.iterator().next();if(origin.getOpcode()!=Opcodes.NEW)continue;String owner=((TypeInsnNode)origin).desc;if(owner.equals(call.owner))continue;Header h=headers.get(owner);
      List<String> path=chain(headers,owner,call.owner,call.desc);if(path==null)continue;
      for(String member:path)bridges.computeIfAbsent(member,k->new HashSet<>()).add(call.desc);call.owner=owner;dirty=true;repaired++;
     }
    }
    if(dirty){ClassWriter writer=new ClassWriter(ClassWriter.COMPUTE_MAXS);cls.accept(writer);changed.put(entry.getName(),writer.toByteArray());}
   }
   try(ZipOutputStream output=new ZipOutputStream(Files.newOutputStream(Paths.get(args[1]),StandardOpenOption.CREATE_NEW))){
    for(ZipEntry entry:entries){byte[] data=changed.get(entry.getName());if(data==null)data=read(input,entry);String name=entry.getName().endsWith(".class")?entry.getName().substring(0,entry.getName().length()-6):"";
     if(bridges.containsKey(name)){ClassNode cls=node(data,0);for(String desc:bridges.get(name))cls.methods.add(bridge(cls.superName,desc));ClassWriter writer=new ClassWriter(ClassWriter.COMPUTE_MAXS);cls.accept(writer);data=writer.toByteArray();}
     output.putNextEntry(new ZipEntry(entry.getName()));output.write(data);output.closeEntry();
    }
   }
  }
  System.err.println("PADBRIDGE_DEX_DIRECT_SUPER_CONSTRUCTORS="+repaired);
 }
}
