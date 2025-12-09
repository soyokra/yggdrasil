# 字节码分析

## 类字节码内容
.java文件编译为.class字节码文件

```
javac Test.java
```

Test.class
```
cafe babe 0000 0045 000d 0a00 0200 0307
0004 0c00 0500 0601 0010 6a61 7661 2f6c
616e 672f 4f62 6a65 6374 0100 063c 696e
6974 3e01 0003 2829 5607 0008 0100 0454
6573 7401 0004 436f 6465 0100 0f4c 696e
654e 756d 6265 7254 6162 6c65 0100 0a53
6f75 7263 6546 696c 6501 0009 5465 7374
2e6a 6176 6100 2100 0700 0200 0000 0000
0100 0100 0500 0600 0100 0900 0000 1d00
0100 0100 0000 052a b700 01b1 0000 0001
000a 0000 0006 0001 0000 0001 0001 000b
0000 0002 000c
```

内容格式
```
魔数(4字节) → 版本号(4字节) → 常量池(可变长) → 访问标志(2字节) → 类索引(2) → 父类索引(2) → 接口表(可变长) → 字段表(可变长) → 方法表(可变长) → 属性表(可变长)
```

## 结构化反解析
字节码文件是16进制内容，难以阅读，通过javap命令反解析为结构化内容
```
javap -verbose -p Test.class
```

输出：
```
Classfile /D:/zcp/github/sprival/Test.class
  Last modified 2025-12-3; size 182 bytes
  MD5 checksum d6dc1d90552979d6334fe238ab963545
  Compiled from "Test.java"
public class Test
  minor version: 0
  major version: 69
  flags: ACC_PUBLIC, ACC_SUPER
Constant pool:
   #1 = Methodref          #2.#3          // java/lang/Object."<init>":()V
   #2 = Class              #4             // java/lang/Object
   #3 = NameAndType        #5.#6          // "<init>":()V
   #4 = Utf8               java/lang/Object
   #5 = Utf8               <init>
   #6 = Utf8               ()V
   #7 = Class              #8             // Test
   #8 = Utf8               Test
   #9 = Utf8               Code
  #10 = Utf8               LineNumberTable
  #11 = Utf8               SourceFile
  #12 = Utf8               Test.java
{
  public Test();
    descriptor: ()V
    flags: ACC_PUBLIC
    Code:
      stack=1, locals=1, args_size=1
         0: aload_0
         1: invokespecial #1                  // Method java/lang/Object."<init>":()V
         4: return
      LineNumberTable:
        line 1: 0
}
SourceFile: "Test.java"

```

## 字节码示例集合

以下示例按特性分类，每个示例专注于特定的Java特性，便于学习和理解字节码结构。每个示例都包含完整的源代码、结构化反解析输出和详细说明。

### 示例1：字段示例（FieldExample）

演示各种类型的字段定义：静态字段、实例字段、基本类型、对象类型、数组、final字段等。

**详细分析**：[字节码分析-字段.md](字节码分析-字段.md)

---

### 示例2：类加载机制示例（ClassLoadingExample）

演示类加载阶段的静态变量和静态代码块机制，重点研究`<clinit>`方法的生成和执行顺序。

**详细分析**：[字节码分析-类加载机制.md](字节码分析-类加载机制.md)

---

### 示例3：方法示例（MethodExample）

演示构造方法、实例方法、静态方法、方法重载的字节码实现。

**详细分析**：[字节码分析-方法.md](字节码分析-方法.md)

---

### 示例4：继承示例（InheritanceExample）

演示继承、方法重写、super调用的底层机制。

**详细分析**：[字节码分析-继承.md](字节码分析-继承.md)

---

### 示例5：控制流示例（ControlFlowExample）

演示if-else、switch、for循环、while循环、增强for循环的字节码转换。

**详细分析**：[字节码分析-控制流.md](字节码分析-控制流.md)

---

### 示例6：异常处理示例（ExceptionExample）

演示try-catch-finally、throws声明的异常表机制。

**详细分析**：[字节码分析-异常处理.md](字节码分析-异常处理.md)

---

### 示例7：Lambda表达式示例（LambdaExample）

演示Java 8 Lambda表达式的invokedynamic实现。

**详细分析**：[字节码分析-Lambda表达式.md](字节码分析-Lambda表达式.md)

---

### 示例8：方法引用示例（MethodReferenceExample）

演示Java 8方法引用的invokedynamic实现。

**详细分析**：[字节码分析-方法引用.md](字节码分析-方法引用.md)

---

### 示例9：泛型示例（GenericExample）

演示泛型类、泛型方法的类型擦除和Signature属性。

**详细分析**：[字节码分析-泛型.md](字节码分析-泛型.md)

---

### 示例10：内部类示例（InnerClassExample）

演示成员内部类、静态内部类的字节码表示和合成方法。

**详细分析**：[字节码分析-内部类.md](字节码分析-内部类.md)

---

### 示例11：同步示例（SynchronizedExample）

演示synchronized方法和同步代码块的实现机制。

**详细分析**：[字节码分析-同步.md](字节码分析-同步.md)

---

### 示例12：可变参数示例（VarargsExample）

演示可变参数方法的ACC_VARARGS标志和数组参数转换。

**详细分析**：[字节码分析-可变参数.md](字节码分析-可变参数.md)

---

## 关键字节码指令速查表

| 指令 | 说明 |
|------|------|
| `aload_0` | 加载局部变量0（this引用） |
| `iload_1` | 加载局部变量1（int类型） |
| `getstatic` | 获取静态字段 |
| `putfield` | 设置实例字段 |
| `invokevirtual` | 调用实例方法 |
| `invokespecial` | 调用构造方法、私有方法或父类方法 |
| `invokestatic` | 调用静态方法 |
| `invokeinterface` | 调用接口方法 |
| `invokedynamic` | 动态调用（Lambda、方法引用） |
| `new` | 创建对象 |
| `dup` | 复制栈顶值 |
| `ldc` | 加载常量 |
| `return` | 返回void |
| `ireturn` | 返回int |
| `areturn` | 返回引用类型 |
| `athrow` | 抛出异常 |
| `goto` | 无条件跳转 |
| `if_icmpge` | int比较，大于等于时跳转 |
| `lookupswitch` | switch语句（稀疏case） |
| `monitorenter` | 获取监视器锁 |
| `monitorexit` | 释放监视器锁 |
| `putstatic` | 设置静态字段 |
| `newarray` | 创建数组 |

## 总结

通过这些拆分的示例，我们可以系统地学习：

1. **字段表**：各种类型的字段在字节码中的表示方式
2. **类加载机制**：静态变量和静态代码块的`<clinit>`方法
3. **方法表**：构造方法、实例方法、静态方法、方法重载的字节码实现
4. **继承和多态**：super调用、方法重写的底层机制
5. **控制流**：if-else、switch、循环结构的字节码转换
6. **异常处理**：try-catch-finally的异常表机制
7. **Java 8特性**：Lambda表达式和方法引用的invokedynamic实现
8. **高级特性**：泛型、内部类、同步、可变参数的字节码表示

理解字节码结构有助于：
- 深入理解Java虚拟机的工作原理
- 优化代码性能
- 调试复杂问题
- 理解Java语言特性的底层实现

所有示例的Java源代码位于 `java/bytecode/` 目录下，javap反解析输出文件位于 `java/bytecode/*_javap.txt`。
