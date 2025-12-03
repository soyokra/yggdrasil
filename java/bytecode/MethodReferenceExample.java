package java.bytecode;

import java.util.ArrayList;
import java.util.List;

/**
 * 方法引用示例 - 演示Java 8方法引用
 */
public class MethodReferenceExample {
    
    // 静态方法引用示例
    public void staticMethodReferenceExample() {
        List<String> list = new ArrayList<>();
        list.add("A");
        list.add("B");
        list.forEach(System.out::println);
    }
    
    // 实例方法引用示例
    public void instanceMethodReferenceExample() {
        List<String> list = new ArrayList<>();
        list.add("hello");
        list.add("world");
        list.forEach(String::toUpperCase);
    }
    
    // 构造方法引用示例
    public void constructorReferenceExample() {
        List<String> list = new ArrayList<>();
        list.add("1");
        list.add("2");
        list.stream()
            .map(Integer::new)
            .forEach(System.out::println);
    }
}

