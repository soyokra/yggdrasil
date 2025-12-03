package java.bytecode;

/**
 * 内部类示例 - 演示成员内部类、静态内部类
 */
public class InnerClassExample {
    
    private int outerField = 100;
    private static int staticOuterField = 200;
    
    // 成员内部类
    public class InnerClass {
        private int innerField;
        
        public InnerClass(int innerField) {
            this.innerField = innerField;
        }
        
        public void innerMethod() {
            System.out.println("InnerClass.innerMethod(): " + innerField);
            System.out.println("Access outer field: " + outerField);
        }
    }
    
    // 静态内部类
    public static class StaticInnerClass {
        private static int staticInnerField = 300;
        
        public static void staticInnerMethod() {
            System.out.println("StaticInnerClass.staticInnerMethod()");
            System.out.println("Static outer field: " + staticOuterField);
        }
        
        public void instanceMethod() {
            System.out.println("StaticInnerClass.instanceMethod()");
        }
    }
    
    public void createInnerClass() {
        InnerClass inner = new InnerClass(50);
        inner.innerMethod();
    }
}

