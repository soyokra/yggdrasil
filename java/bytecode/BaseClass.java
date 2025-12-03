package java.bytecode;

/**
 * 基础父类，包含可重写的方法和字段
 */
public class BaseClass {
    protected String baseField = "BaseClass";
    
    public BaseClass() {
        System.out.println("BaseClass constructor");
    }
    
    public BaseClass(String message) {
        this.baseField = message;
    }
    
    public void baseMethod() {
        System.out.println("BaseClass.baseMethod()");
    }
    
    protected void protectedMethod() {
        System.out.println("BaseClass.protectedMethod()");
    }
    
    public String getBaseField() {
        return baseField;
    }
}

