package java.bytecode;

/**
 * 示例接口，包含方法声明和Java 8的默认方法
 */
public interface ExampleInterface {
    // 接口常量
    int INTERFACE_CONSTANT = 100;
    
    // 抽象方法
    void interfaceMethod();
    
    // Java 8 默认方法
    default void defaultMethod() {
        System.out.println("ExampleInterface.defaultMethod()");
    }
    
    // Java 8 静态方法
    static void staticMethod() {
        System.out.println("ExampleInterface.staticMethod()");
    }
}

