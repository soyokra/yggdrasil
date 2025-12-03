package java.bytecode;

import java.bytecode.BaseClass;

/**
 * 继承示例 - 演示继承、方法重写、super调用
 */
public class InheritanceExample extends BaseClass {
    
    private String childField = "Child";
    
    public InheritanceExample() {
        super();
    }
    
    public InheritanceExample(String message) {
        super(message);
    }
    
    // 重写父类方法
    @Override
    public void baseMethod() {
        super.baseMethod();
        System.out.println("InheritanceExample.baseMethod()");
    }
    
    // 调用父类protected方法
    public void callProtectedMethod() {
        protectedMethod();
    }
    
    public String getChildField() {
        return childField;
    }
}

