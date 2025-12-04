package java.bytecode;

/**
 * 类加载机制示例 - 演示静态变量和静态代码块的字节码
 * 重点研究类加载阶段的初始化机制
 */
public class ClassLoadingExample {
    
    // 静态变量 - 基本类型（带初始值）
    private static int staticInt = 10;
    
    // 静态变量 - 基本类型（不带初始值，使用默认值）
    private static long staticLong;
    
    // 静态变量 - 对象类型
    private static String staticString = "Hello";
    
    // 静态final常量（编译时常量）
    public static final int STATIC_FINAL_CONSTANT = 100;
    
    // 静态final变量（需要运行时初始化）
    private static final String STATIC_FINAL_VAR;
    
    // 静态变量 - 数组
    private static int[] staticArray = new int[]{1, 2, 3};
    
    // 第一个静态代码块
    static {
        System.out.println("第一个静态代码块执行");
        staticInt = 20;
        staticLong = 100L;
    }
    
    // 第二个静态代码块（演示多个静态代码块的执行顺序）
    static {
        System.out.println("第二个静态代码块执行");
        STATIC_FINAL_VAR = "Initialized in static block";
        staticInt = 30;
    }
    
    // 第三个静态代码块
    static {
        System.out.println("第三个静态代码块执行");
        staticString = "World";
    }
    
    // 实例变量（用于对比）
    private int instanceInt = 50;
    
    // 构造方法
    public ClassLoadingExample() {
        System.out.println("构造方法执行");
        this.instanceInt = 100;
    }
    
    // 实例方法
    public void instanceMethod() {
        System.out.println("实例方法执行，staticInt = " + staticInt);
    }
    
    // 静态方法
    public static void staticMethod() {
        System.out.println("静态方法执行，staticInt = " + staticInt);
    }
    
    // 获取静态变量
    public static int getStaticInt() {
        return staticInt;
    }
    
    public static String getStaticFinalVar() {
        return STATIC_FINAL_VAR;
    }
}

