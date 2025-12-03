package java.bytecode;

/**
 * 方法示例 - 演示构造方法、实例方法、静态方法、方法重载
 */
public class MethodExample {
    
    private int value;
    
    // 无参构造方法
    public MethodExample() {
        this.value = 0;
    }
    
    // 有参构造方法
    public MethodExample(int value) {
        this.value = value;
    }
    
    // 实例方法
    public void instanceMethod() {
        System.out.println("instanceMethod()");
    }
    
    // 方法重载 - int参数
    public void instanceMethod(int param) {
        System.out.println("instanceMethod(int): " + param);
    }
    
    // 方法重载 - String参数
    public void instanceMethod(String param) {
        System.out.println("instanceMethod(String): " + param);
    }
    
    // 静态方法
    public static void staticMethod() {
        System.out.println("MethodExample.staticMethod()");
    }
    
    // 返回类型的方法
    public int getValue() {
        return value;
    }
    
    public void setValue(int value) {
        this.value = value;
    }
}

